import unittest
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analisador_oportunidades import calcular_score, classificar, gerar_metricas, carregar_dados

class TestAnalisadorOportunidades(unittest.TestCase):

    def test_calcular_score(self):
        # Teste 1: Cenário básico com valores médios
        row1 = pd.Series({"total_reviews": 25, "empresas": 10, "nota_media": 3.5})
        pesos = {"demanda": 0.4, "concorrencia": 0.3, "satisfacao": 0.3}
        score1 = calcular_score(row1, pesos)
        self.assertAlmostEqual(score1, 0.44, places=3)

        # Teste 2: Alta demanda, baixa concorrência, alta satisfação (score alto)
        row2 = pd.Series({"total_reviews": 50, "empresas": 1, "nota_media": 1.0})
        score2 = calcular_score(row2, pesos)
        self.assertAlmostEqual(score2, 0.925, places=3)

        # Teste 3: Baixa demanda, alta concorrência, baixa satisfação (score baixo)
        row3 = pd.Series({"total_reviews": 0, "empresas": 20, "nota_media": 5.0})
        score3 = calcular_score(row3, pesos)
        self.assertAlmostEqual(score3, 0.0, places=3)

        # Teste 4: total_reviews acima do limite (deve ser limitado a 1.0)
        row4 = pd.Series({"total_reviews": 100, "empresas": 10, "nota_media": 3.5})
        score4 = calcular_score(row4, pesos)
        self.assertAlmostEqual(score4, 0.64, places=3)

        # Teste 5: empresas acima do limite (deve ser limitado a 1.0)
        row5 = pd.Series({"total_reviews": 25, "empresas": 40, "nota_media": 3.5})
        score5 = calcular_score(row5, pesos)
        self.assertAlmostEqual(score5, 0.29, places=3)

        # Teste 6: nota_media nula ou zero
        row6 = pd.Series({"total_reviews": 25, "empresas": 10, "nota_media": 0})
        score6 = calcular_score(row6, pesos)
        self.assertAlmostEqual(score6, 0.65, places=3)

    def test_classificar(self):
        limites = {"alta": 0.66, "media": 0.4}
        self.assertEqual(classificar(0.7, limites), "Alta")
        self.assertEqual(classificar(0.5, limites), "Média")
        self.assertEqual(classificar(0.3, limites), "Baixa")
        self.assertEqual(classificar(0.66, limites), "Alta")
        self.assertEqual(classificar(0.4, limites), "Média")

    def test_gerar_metricas(self):
        data = {
            "cidade": ["CidadeA", "CidadeA", "CidadeB", "CidadeB", "CidadeA"],
            "nicho": ["NichoX", "NichoY", "NichoX", "NichoY", "NichoX"],
            "nome": ["Empresa1", "Empresa2", "Empresa3", "Empresa4", "Empresa5"],
            "nota": [5, 4, 3, 2, 1],
            "reviews": [10, 20, 30, 40, 50]
        }
        df = pd.DataFrame(data)
        resumo_df = gerar_metricas(df)

        self.assertIsInstance(resumo_df, pd.DataFrame)
        self.assertFalse(resumo_df.empty)
        self.assertIn("empresas", resumo_df.columns)
        self.assertIn("nota_media", resumo_df.columns)
        self.assertIn("total_reviews", resumo_df.columns)
        self.assertIn("pct_baixa_qualidade", resumo_df.columns)
        self.assertIn("pct_sem_reviews", resumo_df.columns)

        # Verificar valores específicos
        # CidadeA, NichoX
        self.assertEqual(resumo_df[(resumo_df["cidade"] == "CidadeA") & (resumo_df["nicho"] == "NichoX")]["empresas"].iloc[0], 2)
        self.assertAlmostEqual(resumo_df[(resumo_df["cidade"] == "CidadeA") & (resumo_df["nicho"] == "NichoX")]["nota_media"].iloc[0], 3.0)
        self.assertEqual(resumo_df[(resumo_df["cidade"] == "CidadeA") & (resumo_df["nicho"] == "NichoX")]["total_reviews"].iloc[0], 60)
        self.assertAlmostEqual(resumo_df[(resumo_df["cidade"] == "CidadeA") & (resumo_df["nicho"] == "NichoX")]["pct_baixa_qualidade"].iloc[0], 50.0)

        # CidadeA, NichoY
        self.assertEqual(resumo_df[(resumo_df["cidade"] == "CidadeA") & (resumo_df["nicho"] == "NichoY")]["empresas"].iloc[0], 1)
        self.assertAlmostEqual(resumo_df[(resumo_df["cidade"] == "CidadeA") & (resumo_df["nicho"] == "NichoY")]["nota_media"].iloc[0], 4.0)
        self.assertEqual(resumo_df[(resumo_df["cidade"] == "CidadeA") & (resumo_df["nicho"] == "NichoY")]["total_reviews"].iloc[0], 20)
        self.assertAlmostEqual(resumo_df[(resumo_df["cidade"] == "CidadeA") & (resumo_df["nicho"] == "NichoY")]["pct_baixa_qualidade"].iloc[0], 0.0)

    def test_carregar_dados(self):
        # Criar um arquivo CSV temporário para teste
        test_csv_content = """
cidade,nicho,nome,nota,reviews
CidadeA,NichoX,Empresa1,4.5,100
CidadeA,NichoX,Empresa2,3.0,50
CidadeB,NichoY,Empresa3,,20
CidadeC,NichoZ,Empresa4,5.0,0
CidadeD,NichoW,,2.0,10
"""
        test_file_path = os.path.join(os.getcwd(), "test_input.csv")
        with open(test_file_path, "w", encoding="utf-8-sig") as f:
            f.write(test_csv_content)

        df = carregar_dados(test_file_path)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 4) # Empresa com nome vazio deve ser removida
        self.assertAlmostEqual(df.loc[2, "nota"], 0.0) # Nota nula deve ser preenchida com 0
        self.assertAlmostEqual(df.loc[3, "reviews"], 0.0) # Reviews nulos devem ser preenchidos com 0

        # Testar arquivo não encontrado
        df_nao_encontrado = carregar_dados("arquivo_inexistente.csv")
        self.assertTrue(df_nao_encontrado.empty)

        # Testar arquivo com colunas faltando
        test_csv_content_missing_cols = """
cidade,nicho,nome
CidadeA,NichoX,Empresa1
"""
        test_file_path_missing_cols = os.path.join(os.getcwd(), "test_input_missing.csv")
        with open(test_file_path_missing_cols, "w", encoding="utf-8-sig") as f:
            f.write(test_csv_content_missing_cols)
        df_missing_cols = carregar_dados(test_file_path_missing_cols)
        self.assertTrue(df_missing_cols.empty)

        # Limpar arquivos temporários
        os.remove(test_file_path)
        os.remove(test_file_path_missing_cols)

if __name__ == '__main__':
    unittest.main()