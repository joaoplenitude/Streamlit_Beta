# -*- coding: utf-8 -*-
import pandas as pd
import math
import argparse
import os

def calcular_taxa_fixa_ml(preco_venda):
    """Calcula a taxa fixa do Mercado Livre com base no preço de venda."""
    if preco_venda <= 29.00:
        return 3.00
    elif 29.01 <= preco_venda <= 50.00:
        return 3.50
    elif 50.01 <= preco_venda <= 79.00:
        return 4.00
    else:
        return 0.00 # Acima de R$ 79, não há taxa fixa, entra o frete

def calcular_frete_ml(preco_venda, peso_g):
    """Calcula o custo de frete do Mercado Livre com base no preço de venda e peso."""
    if preco_venda <= 79.00:
        return 0.00 # Frete só se aplica acima de R$ 79

    if peso_g <= 300:
        return 19.95
    elif 300 < peso_g <= 500:
        return 21.45
    elif 500 < peso_g <= 1000:
        return 22.45
    elif 1000 < peso_g <= 2000:
        return 23.45
    elif 2000 < peso_g <= 3000:
        return 24.95
    elif 3000 < peso_g <= 4000:
        return 26.95
    elif 4000 < peso_g <= 5000:
        return 28.45
    else: # Acima de 5kg
        # A tabela fornecida não especifica acima de 5kg, usando a última faixa como padrão.
        # Idealmente, confirmar essa regra ou adicionar lógica para kg adicional se existir.
        print(f"Aviso: Peso {peso_g}g excede a tabela de frete ML fornecida (máx 5kg). Usando taxa de R$ 28,45.")
        return 28.45

def calcular_taxa_fixa_amazon(preco_venda):
    """Calcula a taxa fixa da Amazon com base no preço de venda."""
    if preco_venda <= 30.00:
        return 4.50
    elif 30.01 <= preco_venda <= 78.99:
        return 8.00
    else:
        return 0.00 # Acima de R$ 78.99, não há taxa fixa, entra o frete

def calcular_frete_amazon(preco_venda, peso_g):
    """Calcula o custo de frete da Amazon com base no preço de venda e peso."""
    if preco_venda < 79.00:
        return 0.00 # Frete só se aplica a partir de R$ 79

    if peso_g <= 0:
         print("Aviso: Peso inválido ou zero detectado. Usando a menor taxa de frete Amazon (R$ 15,94).")
         return 15.94
    elif 0 < peso_g <= 249:
        return 15.94
    elif 249 < peso_g <= 499:
        return 16.94
    elif 499 < peso_g <= 999:
        return 17.94
    elif 999 < peso_g <= 1990: # 1.99kg
        return 18.44
    elif 1990 < peso_g <= 2990: # 2.99kg
        return 21.69
    elif 2990 < peso_g <= 3990: # 3.99kg
        return 22.94
    elif 3990 < peso_g <= 4990: # 4.99kg
        return 28.44
    elif 4990 < peso_g <= 5990: # 5.99kg
        return 31.30
    elif 5990 < peso_g <= 6990: # 6.99kg
        return 33.13
    elif 6990 < peso_g <= 7990: # 7.99kg
        return 33.94
    elif 7990 < peso_g <= 8990: # 8.99kg
        return 40.29
    elif 8990 < peso_g <= 9990: # 9.99kg
        return 46.65
    else: # Acima de 9.99kg (9990g)
        # Arredonda para cima o número de kgs adicionais
        kg_adicionais = math.ceil((peso_g - 9990) / 1000)
        frete = 46.65 + (kg_adicionais * 3.50)
        print(f"Aviso: Peso {peso_g}g excede 9.99kg. Calculando frete Amazon com {kg_adicionais}kg adicionais (R$ {frete:.2f}).")
        return frete

def calcular_preco_venda(custo_produto, custo_embalagem, margem_desejada_perc, imposto_perc, peso_g):
    """Calcula o preço de venda necessário para atingir a margem desejada em cada marketplace."""

    # Validação inicial
    if custo_produto < 0 or custo_embalagem < 0 or margem_desejada_perc < 0 or imposto_perc < 0 or peso_g < 0:
        return {"Erro Geral": "Valores de entrada (custo, embalagem, margem, imposto, peso) não podem ser negativos."}

    custo_base = custo_produto + custo_embalagem
    lucro_alvo = custo_base * (margem_desejada_perc / 100.0)
    total_custo_lucro = custo_base + lucro_alvo
    imposto_dec = imposto_perc / 100.0

    resultados = {}

    # --- Shopee --- (20% comissão)
    comissao_shopee_dec = 0.20
    denominador_shopee = 1 - imposto_dec - comissao_shopee_dec
    if denominador_shopee > 1e-6: # Evita divisão por zero ou número muito pequeno
        preco_venda_shopee = total_custo_lucro / denominador_shopee
        lucro_real_shopee = preco_venda_shopee * (1 - imposto_dec - comissao_shopee_dec) - custo_base
        margem_real_shopee = (lucro_real_shopee / custo_base * 100) if custo_base > 1e-6 else 0
        resultados["Shopee"] = {"preco_venda": round(preco_venda_shopee, 2), "lucro_real_rs": round(lucro_real_shopee, 2), "margem_real_perc": round(margem_real_shopee, 2)}
    else:
        resultados["Shopee"] = {"erro": "Imposto + Comissão excedem ou igualam 100%"}

    # --- Shein --- (16% comissão)
    comissao_shein_dec = 0.16
    denominador_shein = 1 - imposto_dec - comissao_shein_dec
    if denominador_shein > 1e-6:
        preco_venda_shein = total_custo_lucro / denominador_shein
        lucro_real_shein = preco_venda_shein * (1 - imposto_dec - comissao_shein_dec) - custo_base
        margem_real_shein = (lucro_real_shein / custo_base * 100) if custo_base > 1e-6 else 0
        resultados["Shein"] = {"preco_venda": round(preco_venda_shein, 2), "lucro_real_rs": round(lucro_real_shein, 2), "margem_real_perc": round(margem_real_shein, 2)}
    else:
        resultados["Shein"] = {"erro": "Imposto + Comissão excedem ou igualam 100%"}

    # --- Mercado Livre --- (17% comissão + Taxa Fixa + Frete)
    comissao_ml_dec = 0.17
    denominador_base_ml = 1 - imposto_dec - comissao_ml_dec
    if denominador_base_ml > 1e-6:
        preco_venda_ml = 0
        preco_estimado = total_custo_lucro / denominador_base_ml # Estimativa inicial
        # Iteração para encontrar o preço que considera taxa fixa e frete
        for i in range(20): # Aumentado limite de iterações
            taxa_fixa_ml = calcular_taxa_fixa_ml(preco_estimado)
            frete_ml = calcular_frete_ml(preco_estimado, peso_g)
            # Verifica se o denominador é válido antes de calcular novo_preco
            if denominador_base_ml <= 1e-6:
                 preco_venda_ml = -1 # Indica erro
                 break
            novo_preco = (total_custo_lucro + taxa_fixa_ml + frete_ml) / denominador_base_ml
            # Condição de parada: diferença pequena ou preço estabilizado
            if abs(novo_preco - preco_estimado) < 0.001:
                preco_venda_ml = novo_preco
                break
            preco_estimado = novo_preco
        else: # Se não convergir após as iterações
             print(f"Aviso ML: Cálculo iterativo não convergiu completamente para custo_base {custo_base}. Usando última estimativa.")
             preco_venda_ml = preco_estimado # Usa a última estimativa

        if preco_venda_ml >= 0:
            taxa_fixa_final_ml = calcular_taxa_fixa_ml(preco_venda_ml)
            frete_final_ml = calcular_frete_ml(preco_venda_ml, peso_g)
            lucro_real_ml = preco_venda_ml * (1 - imposto_dec - comissao_ml_dec) - taxa_fixa_final_ml - frete_final_ml - custo_base
            margem_real_ml = (lucro_real_ml / custo_base * 100) if custo_base > 1e-6 else 0
            resultados["Mercado Livre"] = {"preco_venda": round(preco_venda_ml, 2), "lucro_real_rs": round(lucro_real_ml, 2), "margem_real_perc": round(margem_real_ml, 2)}
        else:
            resultados["Mercado Livre"] = {"erro": "Cálculo falhou (denominador inválido durante iteração)"}
    else:
        resultados["Mercado Livre"] = {"erro": "Imposto + Comissão excedem ou igualam 100%"}

    # --- Amazon --- (15% comissão + Taxa Fixa + Frete)
    comissao_amz_dec = 0.15
    denominador_base_amz = 1 - imposto_dec - comissao_amz_dec
    if denominador_base_amz > 1e-6:
        preco_venda_amz = 0
        preco_estimado = total_custo_lucro / denominador_base_amz
        # Iteração
        for i in range(20):
            taxa_fixa_amz = calcular_taxa_fixa_amazon(preco_estimado)
            frete_amz = calcular_frete_amazon(preco_estimado, peso_g)
            if denominador_base_amz <= 1e-6:
                preco_venda_amz = -1
                break
            novo_preco = (total_custo_lucro + taxa_fixa_amz + frete_amz) / denominador_base_amz
            if abs(novo_preco - preco_estimado) < 0.001:
                preco_venda_amz = novo_preco
                break
            preco_estimado = novo_preco
        else:
            print(f"Aviso Amazon: Cálculo iterativo não convergiu completamente para custo_base {custo_base}. Usando última estimativa.")
            preco_venda_amz = preco_estimado

        if preco_venda_amz >= 0:
            taxa_fixa_final_amz = calcular_taxa_fixa_amazon(preco_venda_amz)
            frete_final_amz = calcular_frete_amazon(preco_venda_amz, peso_g)
            lucro_real_amz = preco_venda_amz * (1 - imposto_dec - comissao_amz_dec) - taxa_fixa_final_amz - frete_final_amz - custo_base
            margem_real_amz = (lucro_real_amz / custo_base * 100) if custo_base > 1e-6 else 0
            resultados["Amazon"] = {"preco_venda": round(preco_venda_amz, 2), "lucro_real_rs": round(lucro_real_amz, 2), "margem_real_perc": round(margem_real_amz, 2)}
        else:
             resultados["Amazon"] = {"erro": "Cálculo falhou (denominador inválido durante iteração)"}
    else:
        resultados["Amazon"] = {"erro": "Imposto + Comissão excedem ou igualam 100%"}

    return resultados

def processar_tabela(arquivo_entrada, arquivo_saida, margem_desejada_perc, custo_embalagem, imposto_perc, coluna_custo, coluna_peso):
    """Lê a tabela de produtos, calcula os preços e salva os resultados."""
    try:
        # Tenta ler como Excel, se falhar, tenta como CSV
        try:
            df = pd.read_excel(arquivo_entrada)
            print(f"Arquivo Excel '{arquivo_entrada}' lido com sucesso.")
        except Exception as e_excel:
            print(f"Falha ao ler como Excel ({e_excel}), tentando como CSV...")
            try:
                # Tenta detectar o separador comum (vírgula ou ponto e vírgula)
                df = pd.read_csv(arquivo_entrada, sep=None, engine='python')
                print(f"Arquivo CSV '{arquivo_entrada}' lido com sucesso.")
            except Exception as e_csv:
                print(f"Erro: Não foi possível ler o arquivo '{arquivo_entrada}' como Excel ou CSV. Verifique o formato e o caminho. Detalhes: {e_csv}")
                return False

        # Verifica se as colunas necessárias existem
        if coluna_custo not in df.columns:
            print(f"Erro: Coluna de custo '{coluna_custo}' não encontrada no arquivo.")
            print(f"Colunas disponíveis: {list(df.columns)}")
            return False
        if coluna_peso not in df.columns:
            print(f"Erro: Coluna de peso '{coluna_peso}' não encontrada no arquivo.")
            print(f"Colunas disponíveis: {list(df.columns)}")
            return False

        resultados_lista = []
        print(f"Processando {len(df)} produtos...")

        for index, row in df.iterrows():
            try:
                custo_produto = float(row[coluna_custo])
                peso_g = float(row[coluna_peso])

                # Verifica se os valores são numéricos e válidos
                if pd.isna(custo_produto) or pd.isna(peso_g):
                    print(f"Aviso: Linha {index+2} ignorada devido a valor não numérico em custo ou peso.")
                    resultados_produto = {"Erro Geral": "Custo ou Peso inválido/não numérico"}
                elif custo_produto < 0 or peso_g < 0:
                     print(f"Aviso: Linha {index+2} ignorada devido a valor negativo em custo ({custo_produto}) ou peso ({peso_g}).")
                     resultados_produto = {"Erro Geral": "Custo ou Peso negativo"}
                else:
                    resultados_produto = calcular_preco_venda(custo_produto, custo_embalagem, margem_desejada_perc, imposto_perc, peso_g)

            except ValueError:
                 print(f"Aviso: Linha {index+2} ignorada. Não foi possível converter custo ('{row[coluna_custo]}') ou peso ('{row[coluna_peso]}') para número.")
                 resultados_produto = {"Erro Geral": "Valor não numérico"}
            except Exception as e:
                 print(f"Erro inesperado ao processar linha {index+2}: {e}")
                 resultados_produto = {"Erro Geral": f"Erro inesperado: {e}"}

            # Adiciona os resultados ao DataFrame original
            for marketplace, data in resultados_produto.items():
                if marketplace == "Erro Geral":
                    df.loc[index, 'Erro Cálculo'] = data
                    break # Sai do loop de marketplaces para este produto
                if "erro" in data:
                    df.loc[index, f'{marketplace} Preço Venda'] = 'Erro'
                    df.loc[index, f'{marketplace} Lucro R$'] = data['erro']
                    df.loc[index, f'{marketplace} Margem %'] = ''
                else:
                    df.loc[index, f'{marketplace} Preço Venda'] = data['preco_venda']
                    df.loc[index, f'{marketplace} Lucro R$'] = data['lucro_real_rs']
                    df.loc[index, f'{marketplace} Margem %'] = data['margem_real_perc']

        # Salva o DataFrame com os resultados em um novo arquivo Excel
        df.to_excel(arquivo_saida, index=False, engine='openpyxl')
        print(f"Processamento concluído. Resultados salvos em '{arquivo_saida}'")
        return True

    except FileNotFoundError:
        print(f"Erro: Arquivo de entrada '{arquivo_entrada}' não encontrado.")
        return False
    except ImportError:
        print("Erro: Biblioteca 'openpyxl' necessária para ler/escrever arquivos Excel não está instalada. Use 'pip install openpyxl'.")
        return False
    except Exception as e:
        print(f"Erro inesperado durante o processamento: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculadora de Preços para Marketplaces')
    parser.add_argument('arquivo_entrada', help='Caminho para o arquivo Excel ou CSV de produtos.')
    parser.add_argument('arquivo_saida', help='Caminho para salvar o arquivo Excel com os resultados.')
    parser.add_argument('--margem', type=float, required=True, help='Margem de lucro desejada (em porcentagem, ex: 30).')
    parser.add_argument('--embalagem', type=float, required=True, help='Custo da embalagem por produto (em R$, ex: 1.50).')
    parser.add_argument('--imposto', type=float, required=True, help='Alíquota de imposto sobre a venda (em porcentagem, ex: 5).')
    parser.add_argument('--coluna_custo', default='Custo', help='Nome da coluna com o preço de custo (padrão: Custo).')
    parser.add_argument('--coluna_peso', default='Peso (g)', help='Nome da coluna com o peso em gramas (padrão: Peso (g)).')

    args = parser.parse_args()

    # Verifica se o diretório de saída existe, se não, cria
    output_dir = os.path.dirname(args.arquivo_saida)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Diretório de saída '{output_dir}' criado.")

    processar_tabela(args.arquivo_entrada, args.arquivo_saida, args.margem, args.embalagem, args.imposto, args.coluna_custo, args.coluna_peso)

