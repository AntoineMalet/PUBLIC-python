import asyncio 
import os 
import re 
import random
from playwright.async_api import async_playwright 
from bs4 import BeautifulSoup 

def clean_html_content(raw_html): 
    """ 
    Nettoie le HTML pour ne garder que la structure propre. 
    Supprime les scripts, les styles intrusifs et les iframes invisibles. 
    """ 
    soup = BeautifulSoup(raw_html, "html.parser") 
    for element in soup(["script", "style", "iframe", "noscript"]): 
        element.extract() 
    return soup.prettify() 

async def search_google_stealth_async(query): 
    print("Initialisation du profil de navigation durci...") 
    user_data_dir = os.path.abspath("./user_data") 
    os.makedirs("HTML", exist_ok=True)
     
    async with async_playwright() as p: 
        context = await p.chromium.launch_persistent_context( 
            user_data_dir=user_data_dir, 
            headless=False, 
            viewport={"width": 1920, "height": 1080}, 
            screen={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            timezone_id="Europe/Paris",
            args=[ 
                "--disable-blink-features=AutomationControlled", 
                "--start-maximized",
                "--disable-features=IsolateOrigins,site-per-process"
            ] 
        ) 
         
        page = context.pages[0] 
        
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)
         
        print("Navigation vers Google...") 
        await page.goto("https://www.google.com", wait_until="domcontentloaded") 
        await asyncio.sleep(2) 
         
        # --- BLOCAGE SÉCURISÉ DU CAPTCHA (AVANT RECHERCHE) --- 
        is_captcha = "captcha" in page.url.lower() or await page.locator("iframe[src*='recaptcha']").is_visible() 
        if is_captcha: 
            print("\n🚨 AIE ! CAPTCHA Détecté sur Google ! Le script est mis en pause.") 
            input("👉 Résolvez le CAPTCHA dans le navigateur, puis appuyez sur ENTRÉE ici...") 
            await asyncio.sleep(1) 

        # --- GESTION DES COOKIES (STRATÉGIE PAR STRUCTURE HTML) --- 
        try: 
            print("Recherche de la fenêtre de consentement...")
            # On cherche directement le dialogue des lois de consentement Google
            cookie_dialog = page.locator('div[role="dialog"]', has_text="Google")
            
            # Cibler spécifiquement le deuxième ou troisième gros bouton de cette modale (souvent "Tout accepter")
            # ou chercher les boutons classiques de cette structure.
            accept_button = page.locator('div[role="dialog"] button').filter(has_text=re.compile(r"Tout accepter|Accept all|J'accepte|I agree", re.IGNORECASE))
            
            if await accept_button.count() == 0:
                # Fallback : Si le texte ne matche pas, on prend le bouton principal de validation de la modale
                accept_button = page.locator('div[role="dialog"] button').last

            print("Tentative de clic sur le bouton de consentement...")
            await accept_button.wait_for(state="visible", timeout=4000)
            await asyncio.sleep(0.5)
            
            # force=True court-circuite les vérifications d'interception de Playwright si le div AG96lb bloque !
            await accept_button.click(force=True) 
            print("Bouton cookies cliqué.") 
            
            # On attend la disparition
            await asyncio.sleep(1.5)
        except Exception as e: 
            print("Pas de modale détectée via la structure (ou déjà validée).") 

        # --- EXÉCUTION DE LA RECHERCHE --- 
        print(f"Saisie de la recherche : '{query}'") 
        search_bar = page.locator("textarea[name='q'], input[name='q']") 
        
        # force=True ici aussi au cas où une ombre de la modale subsiste à l'écran
        await search_bar.click(force=True) 
        await search_bar.fill("") # Clear au cas où
        await search_bar.type(query, delay=random.randint(70, 130)) 
        await asyncio.sleep(0.5)
        await search_bar.press("Enter") 
         
        # Attente des résultats et clic 
        try: 
            print("Attente des résultats de recherche...") 
            await page.wait_for_selector("div#search", timeout=10000) 
             
            if "captcha" in page.url.lower(): 
                print("\n🚨 Second CAPTCHA détecté sur Google après la recherche !") 
                input("👉 Résolvez-le, puis appuyez sur ENTRÉE ici...") 

            first_result = page.locator("div#search h3").first 
            print(f"Option trouvée : '{await first_result.inner_text()}'") 
             
            await first_result.hover() 
            await asyncio.sleep(random.uniform(0.5, 1.0)) 
            await first_result.click() 
             
            # --- MODULE DE SÉCURITÉ SUR LA PAGE CIBLE --- 
            print("Attente de la fin de l'activité réseau sur la page cible...") 
            try: 
                await page.wait_for_load_state("networkidle", timeout=15000)  
            except Exception: 
                print("L'attente réseau a expiré, passage à la vérification anti-bot...") 

            current_url = page.url.lower() 
            current_content = await page.content() 
             
            is_target_captcha = ( 
                "captcha" in current_url  
                or "cloudflare" in current_url  
                or "just a moment" in current_content.lower()  
                or "vérification de votre navigateur" in current_content.lower()
                or "recaptcha" in current_content.lower()
            ) 

            if is_target_captcha: 
                print("\n🚨 SÉCURITÉ : Un CAPTCHA ou Cloudflare bloque l'accès.") 
                input("👉 Résolvez le défi manuellement, attendez l'article, puis appuyez sur ENTRÉE ici...") 
                await page.wait_for_load_state("networkidle", timeout=10000)
             
            print("Extraction et nettoyage du HTML...") 
            raw_html = await page.content() 
            clean_html = clean_html_content(raw_html) 
             
            page_title = await page.title() 
            filename = re.sub(r'(?u)[^-\w.]', '_', page_title) + ".html" 
             
            with open("HTML/" + filename, "w", encoding="utf-8") as f: 
                f.write(clean_html) 
                 
            print(f"🎉 Succès ! Enregistré sous : HTML/{filename}") 
            await asyncio.sleep(2) 
             
        except Exception as e: 
            print(f"\nUne erreur est survenue durant la navigation : {e}") 
            input("Appuyez sur Entrée pour fermer le navigateur...") 
             
        finally: 
            await context.close() 

if __name__ == "__main__": 
    query = "pubmed earthworm ecosystem engineers" 
    asyncio.run(search_google_stealth_async(query))
