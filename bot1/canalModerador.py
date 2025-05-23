MODERATED_CHANNEL_ID = 123456789012345678  # ID do canal moderado
PUBLIC_CHANNEL_ID = 987654321098765432     # ID do canal público

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    infractions = load_infractions()
    guild_data = infractions.setdefault(str(message.guild.id), {"name": message.guild.name, "users": {}})
    user_data = guild_data["users"].setdefault(str(message.author.id), {"infrações": 0, "punições": 0})
    infra_count = user_data["infrações"]

    # Usuários com 3 ou mais infrações só podem escrever no canal moderado
    if infra_count >= 3 and message.channel.id != MODERATED_CHANNEL_ID:
        await message.delete()
        try:
            await message.author.send(
                "Você atingiu 3 ou mais infrações e agora só pode escrever no canal moderado.\n"
                "Por favor, use o canal designado para que suas mensagens sejam revisadas."
            )
        except discord.Forbidden:
            print(f"Não foi possível enviar DM para {message.author}.")
        return

    # Se a mensagem for no canal moderado (revisão manual/automática)
    if message.channel.id == MODERATED_CHANNEL_ID:
        if await check_offensive_gpt(message.content):
            await message.delete()
            try:
                await message.author.send(
                    f"Sua mensagem foi removida por conter linguagem ofensiva (detecção via IA).\n\n"
                    f"**Mensagem analisada:**\n{message.content}\n\n"
                    "Evite o uso de palavras ofensivas, discriminatórias ou agressivas no servidor."
                )
            except discord.Forbidden:
                print("Não foi possível enviar DM.")

            user_data["infrações"] += 1
            save_infractions(infractions)

            if user_data["infrações"] >= 10:
                await ban_user(message.author, message.channel)
            else:
                punishment_time = punishment_times.get(user_data["infrações"], 240)
                if punishment_time == "BAN":
                    await ban_user(message.author, message.channel)
                else:
                    user_data["punições"] += 1
                    save_infractions(infractions)
                    await apply_timeout(message.author, message.channel, punishment_time)
            return

        # Se for uma mensagem segura, copia para o canal público
        public_channel = bot.get_channel(PUBLIC_CHANNEL_ID)
        await public_channel.send(f"{message.author.mention} disse:\n{message.content}")
        await message.delete()
        return

    # Se usuário com menos de 3 infrações, verifica ofensas normalmente
    if await check_offensive_gpt(message.content):
        try:
            await message.delete()
            try:
                await message.author.send(
                    f"Sua mensagem foi removida por conter linguagem ofensiva (detecção via IA).\n\n"
                    f"**Mensagem analisada:**\n{message.content}\n\n"
                    "Evite o uso de palavras ofensivas, discriminatórias ou agressivas no servidor."
                )
            except discord.Forbidden:
                print(f"Não foi possível enviar DM para {message.author}.")
            try:
                await message.channel.send(f"{message.author.mention}, sua mensagem foi removida por conter linguagem imprópria.")
            except discord.Forbidden:
                print("Não foi possível enviar mensagem no canal.")

            user_data["infrações"] += 1
            save_infractions(infractions)

            if user_data["infrações"] >= 10:
                await ban_user(message.author, message.channel)
            else:
                punishment_time = punishment_times.get(user_data["infrações"], 240)
                if punishment_time == "BAN":
                    await ban_user(message.author, message.channel)
                else:
                    user_data["punições"] += 1
                    save_infractions(infractions)
                    await apply_timeout(message.author, message.channel, punishment_time)

        except discord.NotFound:
            print("A mensagem já foi apagada.")
    else:
        await bot.process_commands(message)
