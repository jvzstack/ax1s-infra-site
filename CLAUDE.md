# AX1S Infra — website project context

Dit is de broncode van ax1s-infra.com: een statische, donker-thema HTML/CSS/JS-site (geen build-stap, geen framework) voor AX1S Infra, een FinOps & Infrastructure consultancy (Jelle van Zantwijk — Finance & FinOps, Tom Prager — AI Infrastructure). Beide zijn FinOps Certified Practitioner.

## Deploy-pipeline (belangrijk om te weten voordat je iets pusht)

- Git-repo: [github.com/jvzstack/ax1s-infra-site](https://github.com/jvzstack/ax1s-infra-site) (publiek, owner-account `jvzstack`)
- Elke push naar `main` triggert automatisch `.github/workflows/deploy.yml`, dat de site via **SFTP (SSH-sleutel, poort 22)** naar MijnDomein-hosting (Plesk, host `213.249.67.27`, systeemgebruiker `f_000ab99f`, webroot `httpdocs/`) uploadt.
- **Bekende hikkup:** MijnDomein draait Imunify360, dat GitHub Actions' cloud-IP's (Azure) sporadisch blokkeert. Een deploy-run kan daardoor falen (alle 5 retries binnen de workflow mislukken met "Connection timed out"). Dit is **niet een echte fout** — gewoon `gh run rerun <run-id>` uitvoeren (soms 2-3x nodig). Nooit de workflow zelf "repareren" naar aanleiding hiervan, het commando werkt gewoon bij een volgende poging.
- SFTP-host/poort/gebruiker/private-key staan als GitHub Secrets (`SFTP_HOST`, `SFTP_PORT`, `SFTP_USERNAME`, `SFTP_PRIVATE_KEY`) — niet in de repo.
- `httpdocs/` bevat ook een WordPress-installatie (`wp-admin`, `wp-content`, `wp-includes`) en losse bestanden (`AX1S_full_brand.png`, `Archief.zip`) die **niet** bij deze statische site horen en nooit aangeraakt/verwijderd mogen worden. De deploy-workflow overschrijft alleen bestanden die in de git-repo staan (geen `--delete`), dus dat is al veilig.
- Homebrew, `gh` CLI en LibreOffice (voor xlsx-verificatie) staan lokaal geïnstalleerd op deze Mac t.b.v. dit project.
- **Let op:** Homebrew (`/opt/homebrew/bin`) zit niet automatisch in het PATH van een non-interactieve Bash-sessie. Prefix commando's die `brew`, `gh` of `soffice` gebruiken met: `eval "$(/opt/homebrew/bin/brew shellenv zsh)" &&` — anders krijg je "command not found".
- `gh auth status` bevestigt of je al bent ingelogd (staat al ingesteld als account `jvzstack`, HTTPS-protocol). Zo niet: `gh auth login`.

## Site-structuur

- `index.html` — homepage (hero, services, team, FinOps-uitleg, FAQ, contact)
- `wat-is-finops.html`, `finops-glossarium.html` — kennisbank-pagina's ("Begrippenlijst" in alle zichtbare tekst, bestandsnaam bewust ongewijzigd voor SEO)
- `finops-radar.html` — **3-in-1 hub-tool**, zie eigen sectie hieronder voor de precieze flow
- `ai-kosten-calculator.html` — gratis rekentool voor AI/LLM-kosten (model, volume, tokens, caching, groeiprojectie), geen e-mail nodig. Dezelfde reken-/renderlogica zit ook als los "AI-kosten"-modus in finops-radar.html
- `ri-vs-savings-plan-calculator.html` — gratis rekentool, geen e-mail nodig. Dezelfde reken-/renderlogica zit ook als los "RI vs. Savings Plan"-modus in finops-radar.html
- `finops-diensten.html` — 3-koloms diensten/prijzenpagina (Kosteloze Intake / FinOps-as-a-Service / FinOps-traject) + "Pay on Results"-banner (blauw randje) boven de kaarten
- `gratis-tools.html` — hub-pagina die alle gratis tools/downloads bundelt
- `kennismaking.html` — **outreach-landingspagina voor LinkedIn-verkeer** (minimale nav, `noindex`, niet in sitemap, direct contactformulier + Calendly-knop)
- `blog/*.html` — 28 artikelen (incl. één klantcase: 23% besparing, en een FAQ-post "Veelgestelde vragen over cloudkosten en FinOps" met 14 vraag-antwoordparen + FAQPage-schema). De 8 artikelen van 7 sep t/m 7 okt 2026 zijn afgeleid van LinkedIn-posts en hebben een vaste GEO-opbouw: `.key-answer`-blok ("Kort antwoord") bovenaan, kopjes in vraagvorm, een FAQ-blok (3 vragen, zichtbaar + FAQPage-JSON-LD), `BlogPosting` met `sameAs` naar de originele LinkedIn-post en een bronregel. Visuals die niet 16:9 zijn krijgen `article-banner--natural` (geen crop); op de homepage-kaarten stuurt een inline `object-position` de uitsnede.
- `assets/downloads/` — 3 gratis templates: 2x `.xlsx` (Cloud Tagging Taxonomie, Maandelijks Cost Report — beide met een merk-coverpagina en, bij het cost report, werkende formules + conditionele opmaak + grafiek) en 1x `.pdf` (FinOps Quick-Win Checklist — witte achtergrond, logo op een donker blokje)
- `sitemap.xml`, `llms.txt`, `robots.txt` — GEO/SEO-bestanden, up-to-date houden bij nieuwe/gewijzigde pagina's (lastmod-datums alleen bij échte contentwijzigingen ophogen, niet bij pure CSS-tweaks)

Alle pagina's delen hetzelfde design-systeem; zie "Design v2" verderop (tot het redesign live is: donker thema met accent `#0070F3`/`#4DA3FF`, achtergrond `#08090F`, font Manrope, Iconify-iconen). Contactformulier gaat overal naar hetzelfde Formspree-endpoint (`xreowyvp`). Calendly-link (`calendly.com/j-vanzantwijk-ax1s-infra`) staat overal live. GA4 (`G-VZ06WVBT34`) en LinkedIn Insight Tag (partner ID `9506946`) staan sitewide in de `<head>`, direct na de charset-meta.

**Positionering (belangrijk, recent aangescherpt):** de site praat overal over **"cloud- en AI-kosten"**, niet meer over "cloud, SaaS en AI". SaaS blijft alleen staan waar het de *doelgroep* beschrijft ("AX1S Infra helpt SaaS, fintech en digital-first bedrijven..."), nooit meer als kostencategorie. Uitzonderingen die bewust breed/leerboek-correct blijven: `wat-is-finops.html` (algemene FinOps-definitie, volgt de FinOps Foundation) en `finops-glossarium.html` (SaaS-sprawl blijft als naslagterm staan). Hero-kop homepage (v2): "FinOps-driven cost intelligence for Cloud & AI".

**Menu (v2):** de losse "Diensten & opties"-knop en het item "Tools" staan niet meer in het menu (te vol). Menu = FinOps Radar, Insights, Services, FinOps, Team, Contact + "Plan een Gratis Savings Scan" + taalwissel. Tools blijven bereikbaar via de homepage (knopje in de resultaatkaart en sectie "Eerst zelf proberen") en `gratis-tools.html`; `finops-diensten.html` bestaat nog en wordt vanaf de homepage gelinkt. De "Diensten & opties"-knoppen in artikelen en onderaan tool-pagina's zijn gebleven.

**Knop-kleuren:** de vroegere paarse "Diensten & opties"-knoppen zijn overal vervangen door een **rustige witte knop met zachte blauwe gloed** (statisch in rust, iets sterkere gloed + lichte kleurverschuiving bij hover, geen animatie — dat werd als "kermis" ervaren toen het wel geanimeerd was). Gedeelde class-namen: `.nav-cta-secondary`, `.scard-cta-secondary`, `.more-tools-diensten-btn`, `.btn-diensten`. **Goud** (`rgba(212,175,55,...)` randje/gloed) is het aparte accent voor "dit moet er echt uitspringen"-elementen: de Pay on Results-banner op de homepage en de gratis-intake-link onderaan het FinOps Radar-menu.

## Design v2 (merkstijl) en terughalen van de vorige versie

**Status:** het redesign staat op branch `redesign` (gepusht, **nog niet** naar `main`, dus niet live). Pas na expliciet akkoord mergen naar `main`; elke push naar `main` deployt direct. De donkere versie die voor het redesign live stond is vastgelegd als tag **`v1-donker-live`** (ook op GitHub). Terughalen in één keer: `sh .ops/restore-v1.sh` (zet alle bestanden terug naar die tag in één commit op `main`, pushen doe je daarna zelf; getest). Of laat Claude het doen. De server verwijdert geen bestanden, dus nieuwe pagina's blijven daar staan maar zijn niet meer gelinkt.

**Look:** donker navy (`#050c1d`) met cyaan accent (`#19a7ff`) en blauwe knoppen met verloop (`#1aa8ff` naar `#0a66e8`), lettertype Manrope (koppen 800), een korte cyaan streep onder koppen, rustige kaarten. De blauwe **swoosh** uit het logo is het herkenningspunt. Het logo heeft witte letters, dus nav, hero en footer blijven donker.

**Bestanden:**
- `assets/site-v2.css`: op **alle** pagina's geladen, na de paginastijl. Zet de tokens (kleuren), nav, knoppen, footer, verbergt de oude bewegende orbs-canvas (`#bg-canvas`). Klasse `v2-light` op `<body>` geeft lichte inhoudssecties onder een donkere kopband (blogs, wat-is-finops, begrippenlijst, gratis-tools). Klasse `v2-tool` op `<body>` (Radar en beide calculators): donkere kopband (`.tool-band`) met titel, daaronder de tool in een witte kaart op lichte achtergrond; de tokens worden binnen `.wrap` omgedraaid en hardgecodeerde kleuren zijn in `site-v2.css` overschreven. Savings Scan, diensten en kennismaking blijven donker.
- `assets/home-v2.css` + `index.html`: nieuwe homepage, alles onder `.home`. Secties en ankers in volgorde (nav linkt hierheen): hero, `#team` ("Wie we zijn", staat bewust boven de diensten), `#services` (3 manieren: FinOps-as-a-Service, uitgebreid assessment, traject op maat), `#finops` (kort: kop, intro, Inform/Optimize/Operate en link naar wat-is-finops), case (23%), `#self-serve-promo` (tools), `#blog` (alle artikelen, horizontaal), `#team`, `#contact` (Calendly + Formspree-formulier), `#faq`.
- Hero: kopregel **"FinOps-driven cost intelligence for Cloud & AI"** (Engels op NL en EN, bewust gekozen), met direct daaronder de Nederlandse intro "AX1S Infra helpt digital-first bedrijven…". De losse Nederlandse zin "Grip op je cloud- en AI-kosten, vanaf dag één." is op verzoek verwijderd. Achtergrond: canvas met bollen, datalijnen met kleine lichtjes en netwerkstippen (stopt buiten beeld, statisch bij "minder beweging"). Foto's Tom en Jelle als twee ronde foto's onder de resultaatkaart, Tom eerst.
- `.concept/` (niet gedeployed, dot-map): ontwerpreferentie en losse varianten.
- `.ops/restore-v1.sh`: terughaalscript.

**Taal (afgesproken): standaard Engels.** Een bezoeker die van buiten de site op de homepage (`/` of `/index.html`) komt, wordt via een klein inline script bovenin `index.html` doorgestuurd naar `/en/`. Blijft Nederlands wie op de NL-wissel klikt (`assets/lang-switch.js` onthoudt de keuze in `localStorage.axLang`), wie binnen de site navigeert (referrer van dezelfde site), of `?lang=nl` gebruikt. Zoekmachines en link-previews worden niet doorgestuurd (user-agent-check), en alleen de homepage stuurt door; alle andere Nederlandse pagina's (artikelen, tools, `kennismaking.html`) blijven gewoon Nederlands bereikbaar. `hreflang x-default` verwijst nu naar de Engelse versie (pagina's en sitemap, via `.i18n/i18n.py` en `.i18n/make_sitemap.py`). Let op: een JS-redirect op de homepage kan Nederlandse vindbaarheid van de homepage beïnvloeden; bij tegenvallende NL-resultaten dit terugdraaien (script uit `index.html` halen, x-default weer NL).

**Inhoud (afgesproken):** geen colocatie/hardware/Tier III meer, "Consultants" is overal "Specialists" ("FinOps & Infrastructure Specialists"). Rollen: Tom = AI Infrastructure, Jelle = Cloud & Finance. De tekst bij "Uitgebreid assessment" is door de gebruiker goedgekeurd. De homepage-afbeeldingen zijn echte `<img src>` (de oude pagina laadde ze via base64 in JavaScript, slecht voor SEO/GEO). Nieuwe foto's: `assets/team-tom.jpg` (nieuwe foto, uitsnede) en `assets/team-jelle.jpg` (rechtgezet).

### FinOps Radar (`finops-radar.html`) — 3-in-1 hub-tool

Radar is herbouwd tot één hub met een keuzemenu bovenaan (geen automatische quiz meer): **Cloudkosten** (de originele 7-vragen-quiz), **AI-kosten** en **RI vs. Savings Plan** (dezelfde logica als de losse rekentool-pagina's, hier live-updatend zonder de invoervelden opnieuw op te bouwen — belangrijk om focus tijdens typen te behouden). Onder de derde menu-optie staat een **goud-omrande link** naar de gratis intake (`index.html#contact`). Kop/subtekst/eyebrow passen zich per gekozen modus aan via `setModeHeader()`; een "← Andere tool kiezen"-link brengt je terug naar het menu. De cloud-quiz zelf heeft **geen e-mailmuur meer** — resultaat (euro-besparingsrange + bevindingen, toegeschreven aan "Tom & Jelle's inschatting") verschijnt direct na de laatste vraag; het los daaronder staande contactformulier is puur optioneel. De losse pagina's (`ai-kosten-calculator.html`, `ri-vs-savings-plan-calculator.html`) blijven gewoon bestaan en zijn bewust **niet** samengevoegd — dat is expliciet zo gekozen zodat ze apart kunnen blijven scoren op GEO/SEO, terwijl de Radar op de site zelf als hét ene overkoepelende visitekaartje fungeert.

## Tweetalig: NL (root) + EN (`/en/`)

De Nederlandse pagina's in de root zijn de **bron**; `en/` is een gegenereerde spiegel (niet met de hand bewerken, wordt overschreven). Elke pagina heeft rechtsboven in de nav een `NL`/`EN`-pil (`.lang-switch`, stijl in `assets/lang-switch.css`), plus hreflang (nl/en/x-default=NL), EN-canonical, `og:locale en_GB` en vertaalde JSON-LD. `kennismaking.html` (LinkedIn-outreach, noindex) is bewust **niet** vertaald. Downloads in `assets/downloads/` blijven Nederlands (EN-pagina's zeggen "(Dutch version)"). Banners in `assets/banner-*.png/jpg` hebben Nederlandse tekst in de afbeelding zelf.

Workflow na elke wijziging aan NL-tekst (de gebruiker voert dit niet zelf uit, jij doet het):
1. Werk de NL-pagina bij.
2. `python3 -m venv /tmp/i18nvenv && /tmp/i18nvenv/bin/pip install beautifulsoup4` (eenmalig), dan `/tmp/i18nvenv/bin/python .i18n/i18n.py extract`: toont nieuwe/gewijzigde NL-tekstblokken zonder vertaling (`.i18n/missing.json`).
3. Voeg vertalingen toe als `{"<NL-tekst>": "<EN-tekst>"}` in een nieuw `.i18n/tr/bNN.json` (inline markup staat als `{1}...{/1}`-tokens; die moeten identiek terugkomen).
4. Tekst die in `<script>` staat (Radar, calculators, formulier-meldingen) staat in `.i18n/make_js_repl.py`; draai `python3 .i18n/make_js_repl.py` om `js_replacements.json` te regenereren. Gebruik daar typografische apostrofs (’) in EN-tekst, anders breken JS-strings.
5. `/tmp/i18nvenv/bin/python .i18n/i18n.py build` regenereert `en/` en patcht NL-pagina's (idempotent), dan `python3 .i18n/make_sitemap.py` voor sitemap + hreflang.
6. Nieuwe pagina? Voeg hem toe aan `sitemap.xml` (NL), draai build + make_sitemap, en update `llms.txt` (NL + English-sectie).
`.i18n/` begint met een punt, dus de deploy-workflow uploadt het niet; `en/` wordt wel mee-gedeployd.

## Volgende stap (nog niet uitgevoerd)

Tweede leadmagnet naast de Radar productiseren: de **Kosteloze Intake**-kaart (linkerkaart op `finops-diensten.html`) wordt bewust de "high-value, low-scalability"-tegenhanger van de Radar ("laagdrempelig, schaalbaar"). Moet er visueel echt uitspringen tussen de andere twee kaarten — zelfde goud-randje/gloed-behandeling als de Pay on Results-banner en de Radar-menu-link. Daarna links naar deze dienst toevoegen op bijna alle andere pagina's van de site.

## Openstaande punten

- **Geen echte testimonials/social proof.** Nooit quotes verzinnen. De echte case study (23% besparing) is het enige bewijspunt tot er een echte klant-quote is (gebruiker overweegt die ene klant te vragen om toestemming).
- Onbekend bestand `assets/Kopie van Ontwerp zonder titel.png` staat los in de map — vierkante (1080×1080) social-variant van het logo, nog niet opgehelderd of dit blijft staan, verplaatst wordt, of weg mag.

## Werkwijze-voorkeuren die deze gebruiker heeft aangegeven

- Bedrijf zit in opstartfase, werkt primair met **LinkedIn outreach**, mogelijk later paid ads. Site-werk moet dus echt bijdragen aan conversie, niet alleen aan organisch verkeer/GEO.
- Houd CTA's en copy **niet te salesy** — subtiel en to-the-point, geen agressieve verkooppraat.
- Bij twijfel over een designkeuze: klein/subtiel > groot/opdringerig (bijv. "dunner maken", "niet te salesy").
- Altijd eerst lokaal testen in de browser (Claude_Browser-tools) vóór commit; JSON-LD valideren na elke wijziging aan structured data.
- Git-commits alleen na expliciete goedkeuring; elke push triggert direct een live-deploy, dus wees je daarvan bewust.
