# calculadora_modulo.py
import math

def calcular_taxa_fixa_ml(preco_venda):
    if preco_venda <= 29.00:
        return 3.00
    elif preco_venda <= 50.00:
        return 3.50
    elif preco_venda <= 79.00:
        return 4.00
    else:
        return 0.00

def calcular_frete_ml(preco_venda, peso_g, tabela_frete_ml_df):
    if preco_venda <= 79.00:
        return 0.00
    if tabela_frete_ml_df is None or tabela_frete_ml_df.empty:
        return 0.00

    tabela_frete_ml_df = tabela_frete_ml_df.sort_values(by="PesoMaximoG").reset_index(drop=True)
    for _, row in tabela_frete_ml_df.iterrows():
        if peso_g <= row["PesoMaximoG"]:
            return row["CustoFrete"]
    return tabela_frete_ml_df["CustoFrete"].iloc[-1]

def calcular_taxa_fixa_amazon(preco_venda):
    if preco_venda <= 30.00:
        return 4.50
    elif preco_venda <= 78.99:
        return 8.00
    else:
        return 0.00

def calcular_frete_amazon(preco_venda, peso_g, tabela_frete_amazon_df):
    if preco_venda < 79.00:
        return 0.00
    if tabela_frete_amazon_df is None or tabela_frete_amazon_df.empty:
        return 0.00

    tabela_frete_amazon_df = tabela_frete_amazon_df.sort_values(by="PesoMaximoG").reset_index(drop=True)
    kg_adicional_row = tabela_frete_amazon_df[tabela_frete_amazon_df["PesoMaximoG"] == -1]
    custo_kg_adicional = kg_adicional_row["CustoFrete"].iloc[0] if not kg_adicional_row.empty else 3.50
    tabela_busca = tabela_frete_amazon_df[tabela_frete_amazon_df["PesoMaximoG"] != -1]

    for _, row in tabela_busca.iterrows():
        if peso_g <= row["PesoMaximoG"]:
            return row["CustoFrete"]

    if not tabela_busca.empty:
        ultimo_limite = tabela_busca["PesoMaximoG"].iloc[-1]
        ultimo_custo = tabela_busca["CustoFrete"].iloc[-1]
        kg_extras = math.ceil((peso_g - ultimo_limite) / 1000)
        return ultimo_custo + (kg_extras * custo_kg_adicional)
    return 0.00

def calcular_preco_venda(custo_produto, custo_embalagem, margem_desejada_perc, imposto_perc, peso_g, comissoes_perc, tabela_frete_ml_df, tabela_frete_amazon_df):
    if custo_produto is None or custo_embalagem is None or margem_desejada_perc is None or imposto_perc is None or peso_g is None:
        return {"Erro Geral": "Valor de entrada nulo"}
    if not all(isinstance(v, (int, float)) for v in [custo_produto, custo_embalagem, margem_desejada_perc, imposto_perc, peso_g]):
        return {"Erro Geral": "Valor de entrada não numérico"}
    if custo_produto < 0 or custo_embalagem < 0 or margem_desejada_perc < 0 or imposto_perc < 0 or peso_g < 0:
        return {"Erro Geral": "Valores de entrada negativos"}

    custo_base = custo_produto + custo_embalagem
    lucro_alvo = custo_base * (margem_desejada_perc / 100.0)
    total_custo_lucro = custo_base + lucro_alvo
    imposto_dec = imposto_perc / 100.0
    resultados = {}

    marketplace_funcs = {
        "Mercado Livre": {"fixa_func": calcular_taxa_fixa_ml},
        "Amazon": {"fixa_func": calcular_taxa_fixa_amazon}
    }

    for nome, comissao_perc_val in comissoes_perc.items():
        if not isinstance(comissao_perc_val, (int, float)) or comissao_perc_val < 0:
            resultados[nome] = {"erro": f"Comissão inválida ({comissao_perc_val})"}
            continue

        comissao_dec = comissao_perc_val / 100.0
        denominador_base = 1 - imposto_dec - comissao_dec

        if denominador_base <= 1e-6:
            resultados[nome] = {"erro": "Imposto+Comissão >= 100%"}
            continue

        funcs = marketplace_funcs.get(nome, {"fixa_func": None})
        fixa_func = funcs["fixa_func"]

        tabela_frete_df = None
        frete_func_calculo = None
        if nome == "Mercado Livre":
            tabela_frete_df = tabela_frete_ml_df
            frete_func_calculo = calcular_frete_ml
        elif nome == "Amazon":
            tabela_frete_df = tabela_frete_amazon_df
            frete_func_calculo = calcular_frete_amazon

        if fixa_func is None and frete_func_calculo is None:
            preco_venda = total_custo_lucro / denominador_base
            lucro_real = preco_venda * denominador_base - custo_base
        else:
            preco_estimado = total_custo_lucro / denominador_base
            for _ in range(20):
                taxa_fixa = fixa_func(preco_estimado) if fixa_func else 0
                frete = frete_func_calculo(preco_estimado, peso_g, tabela_frete_df) if frete_func_calculo else 0
                novo_preco = (total_custo_lucro + taxa_fixa + frete) / denominador_base
                if abs(novo_preco - preco_estimado) < 0.001:
                    break
                preco_estimado = novo_preco
            preco_venda = preco_estimado
            taxa_fixa_final = fixa_func(preco_venda) if fixa_func else 0
            frete_final = frete_func_calculo(preco_venda, peso_g, tabela_frete_df) if frete_func_calculo else 0
            lucro_real = preco_venda * denominador_base - taxa_fixa_final - frete_final - custo_base

        margem_real = (lucro_real / custo_base * 100) if custo_base > 1e-6 else 0
        resultados[nome] = {
            "preco_venda": round(preco_venda, 2),
            "lucro_real_rs": round(lucro_real, 2),
            "margem_real_perc": round(margem_real, 2)
        }

    return resultados
