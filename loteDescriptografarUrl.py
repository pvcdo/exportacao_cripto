import base64
import io
import os
import requests
import pandas as pd
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

# Importa o arquivo de variáveis de ambiente
try:
    import env
except ImportError:
    pass

# Importa a lista de configurações do arquivo separado
from config_planilhas import PLANILHAS_CONFIG


def decriptografar_csv(conteudo_base64: str, chave: bytes, iv: bytes) -> str:
    """Decodifica a string Base64 e descriptografa via AES-256-CBC."""
    dados_encriptados = base64.b64decode(conteudo_base64)

    cipher = Cipher(algorithms.AES(chave), modes.CBC(iv))
    decryptor = cipher.decryptor()
    
    dados_com_padding = decryptor.update(dados_encriptados) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    dados_decriptados = unpadder.update(dados_com_padding) + unpadder.finalize()

    return dados_decriptados.decode("utf-8")


def processar_todas_as_planilhas():
    # Carregar chaves do ambiente
    secret_crypto = os.environ.get('secret_crypto')
    iv_crypto = os.environ.get('iv_crypto') or os.environ.get('secret_crypto_iv')

    if not secret_crypto or not iv_crypto:
        raise ValueError("Variáveis 'secret_crypto' ou 'iv_crypto' não foram encontradas no ambiente.")

    KEY = secret_crypto.encode('utf-8')
    IV = iv_crypto.encode('utf-8')

    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    
    sucessos = 0
    falhas = 0

    print("=" * 60)
    print(f"INICIANDO PROCESSAMENTO EM LOTE ({len(PLANILHAS_CONFIG)} PLANILHAS)")
    print("=" * 60)

    for idx, item in enumerate(PLANILHAS_CONFIG, start=1):
        nome_arquivo = item.get("nome_arquivo")
        url_api = item.get("url")

        print(f"\n[{idx}/{len(PLANILHAS_CONFIG)}] Processando: '{nome_arquivo}'")

        try:
            response = requests.get(url_api, allow_redirects=True, timeout=30)

            if response.status_code != 200:
                raise RuntimeError(f"HTTP Status {response.status_code} - {response.text}")

            texto_resposta = response.text.strip()

            if texto_resposta.startswith("<") or "<html" in texto_resposta.lower():
                raise ValueError("A resposta da API retornou uma página HTML de erro/login.")

            if texto_resposta.startswith("Erro:"):
                raise RuntimeError(f"Erro retornado pelo Apps Script: {texto_resposta}")

            # Descriptografia
            csv_resultado = decriptografar_csv(texto_resposta, KEY, IV)

            # Salvar no diretório
            caminho_arquivo_csv = os.path.join(diretorio_atual,'planilhas', nome_arquivo)
            with open(caminho_arquivo_csv, "w", encoding="utf-8") as f:
                f.write(csv_resultado)

            # Prévia rápida no console
            df = pd.read_csv(io.StringIO(csv_resultado))
            print(f" ✅ Salvo em: {caminho_arquivo_csv}")
            print(f" 📊 Registros: {len(df)} linhas | {len(df.columns)} colunas")
            
            sucessos += 1

        except Exception as e:
            print(f" ❌ FALHA ao processar '{nome_arquivo}': {e}")
            falhas += 1

    print("\n" + "=" * 60)
    print(f"RESUMO: Sucessos: {sucessos} | Falhas: {falhas}")
    print("=" * 60)


if __name__ == "__main__":
    processar_todas_as_planilhas()