import discord
import asyncio
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

TOKEN_TESTE = os.getenv("TOKEN_TESTE")
GUILD_ID = int(os.getenv("GUILD_ID_TESTE"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID_TESTE"))

infractions_file = "infractions.json"

# Mensagens para teste
mensagens_de_teste = [
    "Você é horrível!",          # ofensiva
    "Seu inútil de merda",       # ofensiva
    "Bom dia, tudo bem?",        # limpa
    "Seu babaca idiota",         # ofensiva
    "Isso é apenas um teste",    # limpa
    "Você é um lixo humano",     # ofensiva
]

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Bot de teste logado como {client.user}")
    guild = client.get_guild(GUILD_ID)
    channel = guild.get_channel(CHANNEL_ID)

    if channel is None:
        print("Canal não encontrado!")
        await client.close()
        return

    print(f"Enviando mensagens para {channel.name}...\n")

    for mensagem in mensagens_de_teste:
        await channel.send(mensagem)
        print(f"Mensagem enviada: {mensagem}")

        # ⏳ Espera o processamento com verificação contínua por até 15 segundos
        await esperar_infracao(guild, mensagem, timeout=15)

        print("-" * 40)  # separador visual no console

    print("\n✅ Todos os testes concluídos.")
    await client.close()


async def esperar_infracao(guild, mensagem_enviada, timeout=15):
    inicio = time.time()

    while time.time() - inicio < timeout:
        if verificar_infracao_existente(guild, mensagem_enviada):
            print(f"⚠️ Infração detectada para: \"{mensagem_enviada}\"")
            return
        await asyncio.sleep(1)  # Verifica a cada segundo

    print(f"⏳ Tempo esgotado. Nenhuma infração detectada para: \"{mensagem_enviada}\"")


def verificar_infracao_existente(guild, mensagem_enviada):
    if not os.path.exists(infractions_file):
        print("❌ Arquivo de infrações não encontrado!")
        return False

    with open(infractions_file, "r", encoding="utf-8") as file:
        try:
            infractions = json.load(file)
        except json.JSONDecodeError:
            print("❌ Arquivo de infrações corrompido ou incompleto.")
            return False

    server_id = str(guild.id)
    if server_id not in infractions:
        return False

    dados_servidor = infractions[server_id]

    for user_id, info in dados_servidor["users"].items():
        for registro in info["registros"]:
            if mensagem_enviada.strip() == registro["mensagem"].strip():
                # 🔍 Encontrou uma infração referente à mensagem
                print(f"""
👤 Usuário: {info['nome_usuario']}
⚠️ Total de infrações: {info['infrações']}
📑 Registro:
 - [{registro['data']}] {registro['mensagem']}
   📖 Análise: {registro['analise_contexto']}
""")
                return True
    return False


client.run(TOKEN_TESTE)
