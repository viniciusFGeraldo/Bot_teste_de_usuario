import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
import openai
from pathlib import Path
import json
from datetime import datetime, timedelta, timezone
import asyncio
from collections import defaultdict, deque
import re

# Caminho do arquivo JSON para armazenar infrações
infractions_file = "infractions.json"

# Caminho do arquivo JSON para armazenar todas as mensagens
messages_file = "mensagens.json"

# Arquivo JSON para armazenar informações dos servidores
servers_file = "servers.json"

def load_servers():
    if os.path.exists(servers_file):
        with open(servers_file, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

def save_servers(data):
    with open(servers_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_messages():
    if os.path.exists(messages_file):
        with open(messages_file, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

def save_messages(data):
    with open(messages_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)



def load_infractions():
    if os.path.exists(infractions_file):
        with open(infractions_file, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

def save_infractions(data):
    with open(infractions_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def is_ascii_art_or_spam(text):
    # Linha com muitos caracteres especiais (possível ASCII art)
    if sum(1 for c in text if not c.isalnum() and c not in ' \n') > len(text) * 0.4:
        return True

    # Muitas linhas com poucos caracteres (padrão de arte ASCII)
    lines = text.splitlines()
    if len(lines) > 5 and all(len(line.strip()) < 40 for line in lines):
        return True

    # Repetição excessiva de caracteres
    if re.search(r'(.)\1{10,}', text):  # ex: aaaaaaaaaaaa
        return True

    # Comprimento da mensagem
    if len(text) > 1200:
        return True

    return False

# Configuração de tempo de punição (em minutos) para cada infração
punishment_times = {
    1: 1,   # Primeira infração = 1 minuto
    2: 1,   # Segunda infração = 3 minutos
    3: 1,   # Terceira infração = 5 minutos
    4: 1,  # Quarta infração = 10 minutos
    5: 1,  # Quinta infração = 15 minutos
    6: 1,  # Sexta infração = 30 minutos
    7: 1,  # Sétima infração = 1 hora
    8: 1, # Oitava infração = 2 horas
    9: 1, # Nona infração = 4 horas
    10: "BAN" # Décima infração = Banimento
}

# Carrega variáveis do .env
env_path = Path("bot1/.env")
load_dotenv(dotenv_path=env_path)

token = os.getenv("TOKEN")
guild_id = int(os.getenv("GUILD_ID"))
client_id = int(os.getenv("CLIENT_ID"))
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configurações do bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, application_id=client_id)

@bot.event
async def on_guild_join(guild):
    servers = load_servers()

    # Evita duplicação
    if str(guild.id) in servers:
        return

    # Tenta gerar um convite permanente
    try:
        canal = next((c for c in guild.text_channels if c.permissions_for(guild.me).create_instant_invite), None)
        invite = await canal.create_invite(max_age=0, max_uses=0, reason="Convite permanente para registro de servidor") if canal else None
        invite_url = str(invite) if invite else "Sem permissão"
    except Exception as e:
        invite_url = f"Erro: {e}"

    # Obtém o ícone
    icon_url = guild.icon.url if guild.icon else "Nenhum ícone"

    servers[str(guild.id)] = {
        "id_servidor": str(guild.id),
        "server_name": guild.name,
        "icone": icon_url,
        "invite_url": invite_url
    }

    save_servers(servers)
    print(f"Servidor registrado: {guild.name} ({guild.id})")

# Evento de início do bot
@bot.event
async def on_ready():
    print(f'Pronto! Login realizado como {bot.user} (ID: {bot.user.id})')
    print(f'Application ID: {bot.application_id}')

    servers = load_servers()
    for guild in bot.guilds:
        if str(guild.id) not in servers:
            try:
                canal = next((c for c in guild.text_channels if c.permissions_for(guild.me).create_instant_invite), None)
                invite = await canal.create_invite(max_age=0, max_uses=0, reason="Convite permanente") if canal else None
                invite_url = str(invite) if invite else "Sem permissão"
            except Exception as e:
                invite_url = f"Erro: {e}"
            icon_url = guild.icon.url if guild.icon else "Nenhum ícone"
            servers[str(guild.id)] = {
                "id_servidor": str(guild.id),
                "server_name": guild.name,
                "icone": icon_url,
                "invite_url": invite_url
            }
    save_servers(servers)

# Evento de mensagem recebida
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if is_ascii_art_or_spam(message.content):
        try:
            await message.delete()
        except discord.NotFound:
            pass

        # Registra infração como "spam visual" ou "ASCII art"
        infractions = load_infractions()
        server_id = str(message.guild.id)

        if server_id not in infractions:
            infractions[server_id] = {
                "server_name": message.guild.name,
                "icon_url": message.guild.icon.url if message.guild.icon else "Nenhum ícone",
                "invite_url": "Desconhecido",
                "users": {}
            }

        user_data = infractions[server_id]["users"].setdefault(str(message.author.id), {
            "nome_usuario": str(message.author),
            "infrações": 0,
            "punições": 0,
            "registros": []
        })

        user_data["infrações"] += 1
        user_data["registros"].append({
            "motivo": "Spam visual / ASCII art detectado automaticamente",
            "mensagem": message.content,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        })

        save_infractions(infractions)

        await message.channel.send(f"{message.author.mention}, sua mensagem foi removida por conter spam ou arte em texto proibida.")
        return  # Não segue para classificação por IA


    # 🔸 Registro de mensagens gerais (não tem relação com infrações)
    messages = load_messages()
    guild_data = messages.setdefault(str(message.guild.id), {
        "guild_name": message.guild.name,
        "mensagens": []
    })

    registro_mensagem = {
        "usuario_id": str(message.author.id),
        "nome_usuario": str(message.author),
        "canal": message.channel.name if isinstance(message.channel, discord.TextChannel) else "Desconhecido",
        "mensagem": message.content,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

    guild_data["guild_name"] = message.guild.name
    guild_data["mensagens"].append(registro_mensagem)

    save_messages(messages)

    # 🔸 Comando para exibir infrações
    if message.content.lower().startswith("!infracoes"):
        await exibir_infracoes_do_usuario(message)
        return
    
    # 🔍 Função para classificar o contexto da mensagem
    async def classify_message_context(text: str) -> dict:
        prompt = [
            {
                "role": "system",
                "content": (
                    "Você é um moderador de mensagens especializado em entender contexto. "
                    "Classifique a mensagem do usuário de acordo com as seguintes categorias, "
                    "respondendo em formato JSON:\n\n"
                    "{\n"
                    "  'racista': true/false,\n"
                    "  'toxica': true/false,\n"
                    "  'sarcastica': true/false,\n"
                    "  'ironica': true/false,\n"
                    "  'palavra_neutra_em_contexto_toxico': true/false,\n"
                    "  'ofensiva_geral': true/false,\n"
                    "  'conteudo_suspeito_pedofilia': true/false,\n"
                    "  'limpa': true/false,\n"
                    "  'nivel_infracao': 'leve' | 'medio' | 'grave'\n"
                    "}\n\n"
                    "Regras para 'nivel_infracao':\n"
                    "- 'grave': Quando envolver discurso de ódio como racismo, pedofilia (ou conteúdo suspeito relacionado), ou temas de extrema gravidade.\n"
                    "- 'medio': Quando houver mensagens tóxicas, ofensas gerais ou agressividade verbal.\n"
                    "- 'leve': Quando não se enquadrar nas situações acima, mas contenha sarcasmo, ironia, ou uso de palavras neutras em contexto tóxico. Se for uma mensagem limpa, também é classificado como 'leve'.\n\n"
                    "Sobre 'conteudo_suspeito_pedofilia': Sinalize como true caso a mensagem contenha qualquer linguagem suspeita que faça alusão a exploração infantil, assédio a menores, linguagem inapropriada com conotação sexual envolvendo menores ou termos associados.\n\n"
                    "Responda SOMENTE com o JSON, sem comentários adicionais."
                )
            },
            {"role": "user", "content": text},
        ]

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=prompt,
                max_tokens=300,
                temperature=0.0
            )
            content = response.choices[0].message.content.strip()
            content = content.replace("'", '"')  # Garante JSON válido
            return json.loads(content)
        except Exception as e:
            print(f"Erro na classificação contextual: {e}")
            return {}

    # 🔍 Analisa a mensagem
    context_analysis = await classify_message_context(message.content)

    if not context_analysis:
        await bot.process_commands(message)
        return

    # 🔍 Verifica se há alguma infração
    if any([
        context_analysis.get("racista"),
        context_analysis.get("toxica"),
        context_analysis.get("ofensiva_geral"),
        context_analysis.get("palavra_neutra_em_contexto_toxico")
    ]):
        try:
            await message.delete()
        except discord.NotFound:
            pass

        infractions = load_infractions()
        server_id = str(message.guild.id)

        # 🔧 Garante que dados do servidor estão registrados
        if server_id not in infractions:
            try:
                canal = next((c for c in message.guild.text_channels if c.permissions_for(message.guild.me).create_instant_invite), None)
                invite = await canal.create_invite(max_age=0, max_uses=0, reason="Convite permanente") if canal else None
                invite_url = str(invite) if invite else "Sem permissão"
            except:
                invite_url = "Erro ao gerar convite"

            icon_url = message.guild.icon.url if message.guild.icon else "Nenhum ícone"

            infractions[server_id] = {
                "server_name": message.guild.name,
                "icon_url": icon_url,
                "invite_url": invite_url,
                "users": {}
            }

        else:
            infractions[server_id]["server_name"] = message.guild.name
            infractions[server_id]["icon_url"] = message.guild.icon.url if message.guild.icon else "Nenhum ícone"

        # 🔧 Registro de infração do usuário
        guild_data = infractions[server_id]
        user_data = guild_data["users"].setdefault(str(message.author.id), {
            "nome_usuario": str(message.author),
            "infrações": 0,
            "punições": 0,
            "registros": []
        })

        user_data["nome_usuario"] = str(message.author)
        user_data["infrações"] += 1

        registro = {
            "canal": message.channel.name if isinstance(message.channel, discord.TextChannel) else "Desconhecido",
            "mensagem": message.content,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "analise_contexto": context_analysis
        }
        user_data["registros"].append(registro)

        save_infractions(infractions)

        # 🔸 Envia DM para o usuário
        mensagem_dm = (
            f"Sua mensagem foi removida por conter linguagem ofensiva (detecção via IA).\n\n"
            f"**Mensagem analisada:**\n{message.content}\n\n"
            f"🚨 Você já cometeu sua {user_data['infrações']}º infração.\n"
            "Evite o uso de palavras ofensivas, discriminatórias ou agressivas no servidor."
        )

        if message.guild and message.guild.rules_channel:
            mensagem_dm += f"\n\n📜 Você pode consultar as regras do servidor aqui: {message.guild.rules_channel.mention}"

        try:
            await message.author.send(mensagem_dm)
        except discord.Forbidden:
            print(f"Não foi possível enviar DM para {message.author}.")

        # 🔸 Mensagem no canal
        try:
            await message.channel.send(f"{message.author.mention}, sua mensagem foi removida por conter linguagem imprópria.")
        except discord.Forbidden:
            print("Não foi possível enviar mensagem no canal.")

        # 🔸 Aplicação de punição
        if user_data["infrações"] >= 10:
            await ban_user(message.author, message.channel)
        else:
            punishment_time = punishment_times.get(user_data["infrações"], 240)
            if punishment_time == "BAN":
                await ban_user(message.author, message.channel)
            else:
                await apply_timeout(message.author, message.channel, punishment_time)

    else:
        await bot.process_commands(message)

async def apply_timeout(user, channel, duration):
    try:
        await user.timeout(
            datetime.now(timezone.utc) + timedelta(minutes=duration),
            reason=f"Uso de palavras proibidas - Punição de {duration} minutos")
        await send_countdown_popup(user, channel, duration)
    except discord.Forbidden:
        await channel.send(f"🚨 **Erro:** O bot não tem permissão para punir {user.mention}.")
    except Exception as e:
        await channel.send(f"🚨 **Erro ao aplicar punição para {user.mention}:** {e}")

async def send_countdown_popup(user, channel, duration):
    """ Envia um popup com contador regressivo enquanto o usuário estiver silenciado """
    embed = discord.Embed(
        title="⏳ Você está punido!",
        description=f"Você está bloqueado por **{duration} minutos**. Aguarde o tempo expirar.",
        color=discord.Color.red()
    )
    message = await channel.send(f"{user.mention}", embed=embed)

    remaining_time = duration * 60  # Convertendo minutos para segundos
    while remaining_time > 0:
        if remaining_time > 60:
            display_time = f"{remaining_time // 60} minutos"
        else:
            display_time = f"{remaining_time} segundos"

        embed.description = f"⏳ **Tempo restante:** {display_time}"
        await message.edit(embed=embed)
        
        await asyncio.sleep(2)  # Atualiza o tempo a cada 10 segundos
        remaining_time -= 2

    embed.title = "✅ Punição encerrada!"
    embed.description = "Agora você pode enviar mensagens novamente."
    embed.color = discord.Color.green()
    await message.edit(embed=embed)

async def ban_user(user, channel):
    """ Bane o usuário se atingir 10 infrações """
    try:
        await user.ban(reason="Atingiu 10 infrações de mensagens proibidas.")
        await channel.send(f"🚨 {user.mention} foi **banido permanentemente** por atingir 10 infrações.")
    except discord.Forbidden:
        await channel.send(f"🚨 **Erro:** O bot não tem permissão para banir {user.mention}.")
    except Exception as e:
        await channel.send(f"🚨 **Erro ao banir {user.mention}:** {e}")

async def exibir_infracoes_do_usuario(message):
    # Tentar apagar o comando enviado
    try:
        await message.delete()
    except discord.Forbidden:
        pass  # Sem permissão para apagar a mensagem

    # Verificar se o autor é administrador
    if not message.author.guild_permissions.administrator:
        await message.channel.send(f"{message.author.mention}, você não tem permissão para usar este comando.")
        return

    # Separar o comando e argumentos
    args = message.content.split()
    if len(args) < 2:
        await message.channel.send(f"{message.author.mention}, use o comando assim: `!infracoes <ID ou nome do usuário>`")
        return

    usuario_argumento = " ".join(args[1:]).strip().lower()

    try:
        with open("infractions.json", encoding="utf-8") as f:
            infractions = json.load(f)
    except FileNotFoundError:
        await message.channel.send(f"{message.author.mention}, nenhum registro de infração foi encontrado.")
        return

    guild_id = str(message.guild.id)

    if guild_id not in infractions:
        await message.channel.send(f"{message.author.mention}, este servidor não possui dados de infrações.")
        return

    # Procurar usuário por ID ou nome
    user_data = None
    user_id_encontrado = None

    for uid, data in infractions[guild_id]["users"].items():
        if usuario_argumento == uid or usuario_argumento == data.get("nome_usuario", "").lower():
            user_data = data
            user_id_encontrado = uid
            break

    if not user_data:
        await message.channel.send(f"{message.author.mention}, usuário não encontrado nas infrações.")
        return

    registros = user_data.get("registros", [])
    if not registros:
        await message.channel.send(f"{message.author.mention}, o usuário não possui infrações detalhadas registradas.")
        return

    # Criar o texto com as infrações
    texto = f"**👤 Usuário:** {user_data.get('nome_usuario', 'Desconhecido')} (ID: {user_id_encontrado})\n"
    texto += f"**🔢 Infrações:** {user_data.get('infrações', 0)} | **🚫 Punições:** {user_data.get('punições', 0)}\n\n"

    for i, registro in enumerate(registros, 1):
        texto += f"**{i}.** `{registro['data']}` no canal **#{registro['canal']}**\n"
        texto += f"🗨️ _\"{registro['mensagem']}\"_\n\n"

    try:
        await message.author.send("📬 Aqui estão as infrações do usuário solicitado:")
        await message.author.send(texto)
        await message.channel.send(f"{message.author.mention}, as infrações foram enviadas no seu privado. 📥")
    except discord.Forbidden:
        await message.channel.send(f"{message.author.mention}, não consegui te enviar uma DM. Verifique se você permite mensagens diretas do servidor.")

# Tratamento de erros de comando
@bot.event
async def on_command_error(ctx, error):
    print(f"Erro ao executar comando: {error}")

# Comando GPT personalizado
@bot.command()
async def gpt(ctx, *, prompt: str):
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente amigável que responde em português de forma clara e objetiva."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        resposta = response.choices[0].message.content.strip()
        await ctx.send(resposta)
        try:
            await ctx.author.send(resposta)
        except discord.Forbidden:
            print(f"Não foi possível enviar DM para {ctx.author}.")
    except Exception as e:
        print("Erro ao consultar a API da OpenAI:", e)
        await ctx.send("Houve um erro ao consultar o GPT.")

# Inicia o bot
bot.run(token)