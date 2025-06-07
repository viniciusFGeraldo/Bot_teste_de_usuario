import pyautogui as py
import time
import pyperclip

# Localiza o campo de texto na tela
campo_texto = py.locateCenterOnScreen(r"C:\\Bot_Discord_Python_Prototipo-main-0.1.2\\teste\\img\\Capturar.PNG")

# Clica no campo de texto
if campo_texto:
    py.click(campo_texto)
    time.sleep(1)

    # Lista de frases
    frases = [
        "vou papar teu cu até de manhã",
        "galinha, estacionamento de tuneladora",
        "bom dia, seus lindos.",
        "é como dizem, ou você é do grupo que empurra ou do grupo que é empurrado.",
        "quem responder é viado."
    ]

    # Envia cada frase da lista
    for frase in frases:
        pyperclip.copy(frase)
        py.hotkey("ctrl", "v") 
        time.sleep(0.5) 
        py.press("enter")  
        time.sleep(10)

    print("Todas as frases foram enviadas com sucesso!")
else:
    print("Campo de texto NÃO encontrado na tela.")

