import asyncio 
import os 
import re 
import random
from playwright.async_api import async_playwright 
from playwright_stealth import Stealth 
from bs4 import BeautifulSoup 

def clean_html_content(raw_html): 
    """ 
    Nettoie le HTML pour ne garder que la structure propre. 
    Supprime les scripts, les styles intrusifs et les iframes invisibles. 
    """ 
    soup = BeautifulSoup(raw_html, "html.parser") 
     
    # Supprime toutes les balises de scripts JS et de styles CSS 
    for element in soup(["script", "style", "iframe", "noscript"]): 
        element.extract() 
         
    return soup.prettify() 

async def search_google_stealth_async(query): 
    print("Initialisation du profil stealth...") 
    user_data_dir = os.path.abspath("./user_data") 
    
    # S'assurer que le dossier de destination existe
    os.makedirs("HTML", exist_ok=True)
     
    async with Stealth().use_async(async_playwright()) as stealth_p: 
        context = await stealth_p.chromium.launch_persistent_context( 
            user_data_dir=user_data_dir, 
            headless=False, 
            viewport={"width": 1920, "height": 1080}, 
            args=[ 
                "--disable-blink-features=AutomationControlled", 
                "--start-maximized" 
            ] 
        ) 
         
        page = context.pages[0] 
         
        print("Navigation vers Google...") 
        await page.goto("https://www.google.com") 
        await asyncio.sleep(random.uniform(1.5, 3.0)) 
         
        # --- BLOCAGE SÉCURISÉ DU CAPTCHA (AVANT RECHERCHE) --- 
        is_captcha = "captcha" in page.url.lower() or await page.locator("iframe[src*='recaptcha']").is_visible() 
         
        if is_captcha: 
            print("\n🚨 AIE ! CAPTCHA Détecté sur Google ! Le script est mis en pause.") 
            print("👉 Résolvez le CAPTCHA directement dans la fenêtre du navigateur.") 
            input("👉 Une fois que vous voyez la page d'accueil classique de Google, appuyez sur ENTRÉE ici...") 
            print("Reprise du script...") 
            await asyncio.sleep(1) 

        # Gestion des Cookies 
        try: 
            accept_button = page.locator("button:has-text('Accept all'), button:has-text('Tout accepter'), button:has-text('J\'accepte')") 
            if await accept_button.is_visible(timeout=2000): 
                await accept_button.click() 
                print("Cookies acceptés.") 
        except Exception: 
            pass 

        # Exécution de la Recherche 
        print(f"Saisie de la recherche : '{query}'") 
        search_bar = page.locator("textarea[name='q'], input[name='q']") 
        await search_bar.click() 
        await search_bar.type(query, delay=random.randint(80, 150)) # Délai variable plus humain
        await asyncio.sleep(0.5)
        await search_bar.press("Enter") 
         
        # Attente des résultats et clic 
        try: 
            print("Attente des résultats de recherche...") 
            await page.wait_for_selector("div#search", timeout=10000) 
             
            # Vérification : est-ce qu'un second captcha est apparu après la recherche ? 
            if "captcha" in page.url.lower(): 
                print("\n🚨 Second CAPTCHA détecté sur Google après la recherche !") 
                input("👉 Résolvez-le, attendez de voir les résultats, puis appuyez sur ENTRÉE ici...") 

            first_result = page.locator("div#search h3").first 
            print(f"Option trouvée : '{await first_result.inner_text()}'") 
             
            # Simulation d'un comportement humain avant le clic
            await first_result.hover() 
            await asyncio.sleep(random.uniform(0.5, 1.2)) 
            await first_result.click() 
             
            # --- NOUVEAU MODULE DE SÉCURITÉ SUR LA PAGE CIBLE --- 
            print("Attente de la fin de l'activité réseau sur la page cible (networkidle)...") 
            try: 
                # On attend d'abord que la page se charge. Si Cloudflare bloque, 
                # la page va se stabiliser sur le formulaire de défi.
                await page.wait_for_load_state("networkidle", timeout=15000)  
            except Exception: 
                print("L'attente réseau a expiré (possible blocage anti-bot), vérification des sécurités...") 

            # Analyse de la page APRÈS chargement ou expiration
            current_url = page.url.lower() 
            current_content = await page.content() 
             
            is_target_captcha = ( 
                "captcha" in current_url  
                or "cloudflare" in current_url  
                or "just a moment" in current_content.lower()  
                or "vérification de votre navigateur" in current_content.lower()
                or "recaptcha" in current_content.lower()
                or await page.locator("iframe[src*='recaptcha']").is_visible() 
            ) 

            # Si le robot est bloqué par la sécurité de la page cible
            if is_target_captcha: 
                print("\n🚨 SÉCURITÉ : Un CAPTCHA ou une page Cloudflare bloque l'accès à la page finale !") 
                print("👉 Résolvez le défi visuel/Cloudflare directement dans la fenêtre du navigateur.") 
                input("👉 Une fois que la VRAIE page finale (l'article) est affichée, appuyez sur ENTRÉE ici...") 
                print("Reprise et stabilisation finale...") 
                # On ré-attend que la vraie page se stabilise après votre action
                await page.wait_for_load_state("networkidle", timeout=10000)
             
            # Extraction et traitement
            print("Extraction du HTML complet...") 
            raw_html = await page.content() 
             
            print("Nettoyage du code HTML...") 
            clean_html = clean_html_content(raw_html) 
             
            # Générer un nom de fichier propre 
            page_title = await page.title() 
            filename = re.sub(r'(?u)[^-\w.]', '_', page_title) + ".html" 
             
            with open("HTML/" + filename, "w", encoding="utf-8") as f: 
                f.write(clean_html) 
                 
            print(f"🎉 Succès ! Page finale sauvegardée sous : HTML/{filename}") 
            await asyncio.sleep(2) 
             
        except Exception as e: 
            print(f"\nUne erreur est survenue durant la navigation : {e}") 
            input("Appuyez sur Entrée pour fermer le navigateur...") 
             
        finally: 
            await context.close() 

if __name__ == "__main__": 
    query = "pubmed earthworm ecosystem engineers" 
    asyncio.run(search_google_stealth_async(query))