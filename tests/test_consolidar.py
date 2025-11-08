import unittest
import pandas as pd
import os
import shutil
import sys
from unittest.mock import patch, mock_open

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from consolidar import consolidar_dados_empresas_googlemaps, organizar_oportunidades_db, criar_nichos_especificos, limpar_arquivos_antigos, registrar_log_consolidacao

class TestConsolidar(unittest.TestCase):

    def setUp(self):
        self.base_path = os.path.join(os.getcwd(), "test_temp")
        self.results_path = os.path.join(self.base_path, "results")
        self.data_path = os.path.join(self.base_path, "data")
        self.consolidated_path = os.path.join(self.results_path, "consolidados")
        self.csv_path = os.path.join(self.results_path, "csv")
        self.especificos_path = os.path.join(self.consolidated_path, "especificos")

        os.makedirs(self.csv_path, exist_ok=True)
        os.makedirs(self.data_path, exist_ok=True)
        os.makedirs(self.especificos_path, exist_ok=True)

        # Criar arquivos CSV de teste
        self.create_test_csv("dados_empresas_googlemaps_sub_1.csv", "cidade,nicho,nome,nota,reviews\nCidadeA,NichoX,Empresa1,4.0,10\nCidadeA,NichoY,Empresa2,3.5,5")
        self.create_test_csv("dados_empresas_googlemaps_sub_2.csv", "cidade,nicho,nome,nota,reviews\nCidadeB,NichoX,Empresa3,4.2,12\nCidadeA,NichoX,Empresa1,4.0,10") # Duplicata
        # Criar oportunidades.db.csv no diretório data (correto)
        with open(os.path.join(self.data_path, "oportunidades.db.csv"), "w", encoding="utf-8-sig") as f:
            f.write("cidade,nicho,score_oportunidade\nCidadeA,NichoX,0.7\nCidadeA,NichoY,0.3")

    def tearDown(self):
        if os.path.exists(self.base_path):
            shutil.rmtree(self.base_path)

    def create_test_csv(self, filename, content):
        filepath = os.path.join(self.csv_path, filename)
        with open(filepath, "w", encoding="utf-8-sig") as f:
            f.write(content)

    def test_consolidar_dados_empresas_googlemaps(self):
        df_master = consolidar_dados_empresas_googlemaps(self.results_path, self.consolidated_path)
        self.assertIsInstance(df_master, pd.DataFrame)
        self.assertFalse(df_master.empty)
        self.assertEqual(len(df_master), 3) # 4 registros, 1 duplicata
        self.assertTrue(os.path.exists(os.path.join(self.consolidated_path, "dados_empresas_googlemaps_master.csv")))

    def test_organizar_oportunidades_db(self):
        df_oportunidades_sorted, df_melhores_oportunidades = organizar_oportunidades_db(self.data_path)
        self.assertIsInstance(df_oportunidades_sorted, pd.DataFrame)
        self.assertFalse(df_oportunidades_sorted.empty)
        self.assertEqual(df_oportunidades_sorted.iloc[0]["nicho"], "NichoX") # Ordenado por score
        self.assertEqual(len(df_melhores_oportunidades), 1) # Apenas um acima do LIMITE_SCORE (0.63)
        self.assertTrue(os.path.exists(os.path.join(self.data_path, "melhores_oportunidades.db.csv")))

    def test_criar_nichos_especificos(self):
        df_oportunidades = pd.DataFrame({"cidade": ["CidadeA"], "nicho": ["NichoX"], "score_oportunidade": [0.7]})
        df_empresas_master = pd.DataFrame({"cidade": ["CidadeA"], "nicho": ["NichoX"], "nome": ["Empresa1"]})
        criar_nichos_especificos(df_oportunidades, df_empresas_master, self.consolidated_path)
        self.assertTrue(os.path.exists(os.path.join(self.especificos_path, "NichoX_empresas_googlemaps.csv")))

    def test_limpar_arquivos_antigos(self):
        # Criar arquivos para serem limpos (correspondendo ao padrão de busca da função)
        open(os.path.join(self.csv_path, "ranking_oportunidades_sub_1.csv"), "a").close()
        open(os.path.join(self.csv_path, "dados_empresas_googlemaps_sub_3.csv"), "a").close()
        open(os.path.join(self.results_path, "grafico_oportunidades_sub_1.png"), "a").close()

        limpar_arquivos_antigos(self.results_path)

        self.assertFalse(os.path.exists(os.path.join(self.csv_path, "ranking_oportunidades_sub_1.csv")))
        self.assertFalse(os.path.exists(os.path.join(self.csv_path, "dados_empresas_googlemaps_sub_3.csv")))
        self.assertFalse(os.path.exists(os.path.join(self.results_path, "imagens", "grafico_oportunidades_sub_1.png")))

    @patch('consolidar.pd.Timestamp')
    @patch('consolidar.os.path.exists')
    @patch('consolidar.pd.DataFrame.to_csv')
    def test_registrar_log_consolidacao(self, mock_to_csv, mock_exists, mock_timestamp):
        mock_timestamp.now.return_value = pd.Timestamp('2023-10-27 10:00:00')
        mock_exists.return_value = False # Simula que o arquivo de log não existe inicialmente

        registrar_log_consolidacao(self.data_path, 5, 120.5)

        mock_to_csv.assert_called_once_with(
            os.path.join(self.data_path, "log_consolidacao.csv"),
            mode='w',
            header=True,
            index=False
        )

        mock_exists.return_value = True # Simula que o arquivo de log já existe
        mock_to_csv.reset_mock()

        registrar_log_consolidacao(self.data_path, 3, 60.0)

        mock_to_csv.assert_called_once_with(
            os.path.join(self.data_path, "log_consolidacao.csv"),
            mode='a',
            header=False,
            index=False
        )

if __name__ == '__main__':
    unittest.main()