"""Multilingual, principles-first art and music demo curriculum."""

from __future__ import annotations

import json
from copy import deepcopy

import sqlalchemy as sa


LANGUAGES = ("en", "et", "lt", "es")


def _t(en, et, lt, es):
    return {"en": en, "et": et, "lt": lt, "es": es}


CATALOG = [
    {
        "title": _t("Art History", "Kunstiajalugu", "Meno istorija", "Historia del arte"),
        "slug": "art-history",
        "description": _t(
            "Learn how images, objects, and buildings express the ideas of their time—from early civilisations to modernism.",
            "Õpi, kuidas pildid, esemed ja ehitised väljendavad oma ajastu ideid varastest tsivilisatsioonidest modernismini.",
            "Sužinokite, kaip vaizdai, daiktai ir pastatai perteikia savo laikotarpio idėjas – nuo ankstyvųjų civilizacijų iki modernizmo.",
            "Descubre cómo las imágenes, los objetos y los edificios expresan las ideas de su época, desde las primeras civilizaciones hasta el modernismo.",
        ),
        "category": _t("Art History", "Kunstiajalugu", "Meno istorija", "Historia del arte"),
        "difficulty": "beginner",
        "is_published": True,
        "modules": [{
            "title": _t("Seeing Art Across Time", "Kunsti vaatlemine läbi aja", "Meno pažinimas per laiką", "Ver el arte a través del tiempo"),
            "lessons": [
                {
                    "title": _t("From Early Images to Classical Worlds", "Varastest kujutistest antiikmaailmani", "Nuo ankstyvųjų vaizdų iki antikos pasaulio", "De las primeras imágenes al mundo clásico"),
                    "content_md": _t(
                        """# From Early Images to Classical Worlds

Art history asks two questions together: **what do we see?** and **why was it made here and then?** Early cave images used line, colour, and animal forms to preserve knowledge or ritual meaning. Egyptian art connected images with order, memory, and the afterlife. Greek and Roman artists studied proportion, ideal bodies, civic identity, and storytelling.

## A simple looking method

1. **Observe** the material, scale, colour, line, and composition.
2. **Identify** the subject and symbols.
3. **Connect** the work to its maker, audience, place, and purpose.
4. **Interpret** what the choices communicate.

Art is evidence: its materials and visual decisions reveal how people understood power, belief, nature, and themselves.""",
                        """# Varastest kujutistest antiikmaailmani

Kunstiajalugu küsib korraga: **mida me näeme?** ja **miks loodi see just siin ja sel ajal?** Varased koopapildid kasutasid joont, värvi ja loomakujusid teadmiste või rituaalse tähenduse säilitamiseks. Egiptuse kunst sidus kujutised korra, mälu ja surmajärgse eluga. Kreeka ja Rooma kunstnikud uurisid proportsiooni, idealiseeritud keha, kodanikuidentiteeti ja lugude jutustamist.

## Lihtne vaatlusmeetod

1. **Vaatle** materjali, mõõtkava, värvi, joont ja kompositsiooni.
2. **Tuvasta** teema ja sümbolid.
3. **Seosta** teos looja, publiku, koha ja eesmärgiga.
4. **Tõlgenda**, mida need valikud väljendavad.

Kunst on tõendusmaterjal: materjalid ja visuaalsed otsused näitavad, kuidas inimesed mõistsid võimu, usku, loodust ja iseennast.""",
                        """# Nuo ankstyvųjų vaizdų iki antikos pasaulio

Meno istorija vienu metu klausia: **ką matome?** ir **kodėl tai buvo sukurta būtent čia ir tada?** Ankstyvieji urvų piešiniai naudojo liniją, spalvą ir gyvūnų formas žinioms ar ritualinei prasmei išsaugoti. Egipto menas siejo vaizdus su tvarka, atmintimi ir pomirtiniu gyvenimu. Graikų ir romėnų menininkai tyrinėjo proporcijas, idealizuotą kūną, pilietinę tapatybę ir pasakojimą.

## Paprastas stebėjimo metodas

1. **Stebėkite** medžiagą, mastelį, spalvą, liniją ir kompoziciją.
2. **Atpažinkite** temą ir simbolius.
3. **Susiekite** kūrinį su autoriumi, auditorija, vieta ir paskirtimi.
4. **Interpretuokite**, ką perteikia šie pasirinkimai.

Menas yra įrodymas: jo medžiagos ir vizualūs sprendimai atskleidžia, kaip žmonės suvokė galią, tikėjimą, gamtą ir save.""",
                        """# De las primeras imágenes al mundo clásico

La historia del arte pregunta a la vez: **¿qué vemos?** y **¿por qué se creó aquí y entonces?** Las primeras imágenes rupestres usaban línea, color y formas animales para conservar conocimiento o significado ritual. El arte egipcio relacionó las imágenes con el orden, la memoria y la vida después de la muerte. Los artistas griegos y romanos estudiaron la proporción, el cuerpo ideal, la identidad cívica y la narración.

## Un método sencillo para mirar

1. **Observa** el material, la escala, el color, la línea y la composición.
2. **Identifica** el tema y los símbolos.
3. **Relaciona** la obra con su creador, público, lugar y propósito.
4. **Interpreta** qué comunican esas decisiones.

El arte es evidencia: sus materiales y decisiones visuales revelan cómo las personas entendían el poder, la fe, la naturaleza y a sí mismas.""",
                    ),
                    "xp_reward": 25,
                    "duration_min": 18,
                    "quiz": {
                        "title": _t("Early Art Quiz", "Varase kunsti viktoriin", "Ankstyvojo meno testas", "Cuestionario de arte antiguo"),
                        "pass_threshold": 60,
                        "xp_reward": 30,
                        "questions": [
                            {
                                "question_text": _t("What should contextual art history connect an artwork to?", "Millega seostab kontekstuaalne kunstiajalugu teose?", "Su kuo kontekstinė meno istorija sieja kūrinį?", "¿Con qué relaciona una obra la historia del arte contextual?"),
                                "options": _t(["Maker, audience, place, and purpose", "Price only", "Colour only", "The viewer's age"], ["Looja, publik, koht ja eesmärk", "Ainult hind", "Ainult värv", "Vaataja vanus"], ["Autorius, auditorija, vieta ir paskirtis", "Tik kaina", "Tik spalva", "Žiūrovo amžius"], ["Creador, público, lugar y propósito", "Solo el precio", "Solo el color", "La edad del espectador"]),
                                "correct_answer": _t("Maker, audience, place, and purpose", "Looja, publik, koht ja eesmärk", "Autorius, auditorija, vieta ir paskirtis", "Creador, público, lugar y propósito"),
                                "explanation": _t("Context explains how and why visual choices gained meaning.", "Kontekst selgitab, kuidas ja miks visuaalsed valikud tähenduse said.", "Kontekstas paaiškina, kaip ir kodėl vizualūs sprendimai įgijo prasmę.", "El contexto explica cómo y por qué las decisiones visuales adquirieron significado."),
                            },
                            {
                                "question_text": _t("Which idea was especially important in Greek and Roman art?", "Milline idee oli Kreeka ja Rooma kunstis eriti tähtis?", "Kuri idėja buvo ypač svarbi graikų ir romėnų mene?", "¿Qué idea fue especialmente importante en el arte griego y romano?"),
                                "options": _t(["Proportion", "Digital animation", "Photography", "Recorded sound"], ["Proportsioon", "Digitaalne animatsioon", "Fotograafia", "Salvestatud heli"], ["Proporcija", "Skaitmeninė animacija", "Fotografija", "Įrašytas garsas"], ["La proporción", "La animación digital", "La fotografía", "El sonido grabado"]),
                                "correct_answer": _t("Proportion", "Proportsioon", "Proporcija", "La proporción"),
                                "explanation": _t("Classical artists explored proportion in bodies and architecture.", "Antiikkunstnikud uurisid proportsiooni kehades ja arhitektuuris.", "Antikos menininkai tyrinėjo kūno ir architektūros proporcijas.", "Los artistas clásicos exploraron la proporción en el cuerpo y la arquitectura."),
                            },
                        ],
                    },
                },
                {
                    "title": _t("Renaissance to Modernism", "Renessansist modernismini", "Nuo Renesanso iki modernizmo", "Del Renacimiento al modernismo"),
                    "content_md": _t(
                        """# Renaissance to Modernism

Renaissance artists revived classical ideas while developing linear perspective, close observation, and new forms of patronage. Baroque art intensified movement, drama, and contrast. During the nineteenth century, industrialisation, photography, cities, and political change challenged inherited rules.

Modernism is not one style. Impressionists studied changing light; Cubists showed several viewpoints at once; abstraction made colour, shape, and rhythm subjects in themselves.

When comparing works, track **continuity and change**: What tradition remains? What has changed in technique, audience, subject, or purpose? A movement becomes clearer when understood as a response to earlier art and to its own social world.""",
                        """# Renessansist modernismini

Renessansikunstnikud taaselustasid antiigi ideid ning arendasid lineaarperspektiivi, tähelepanelikku vaatlust ja uusi metseenluse vorme. Barokikunst võimendas liikumist, draamat ja kontrasti. 19. sajandil seadsid tööstus, fotograafia, linnad ja poliitilised muutused pärandatud reeglid kahtluse alla.

Modernism ei ole üks stiil. Impressionistid uurisid muutuvat valgust, kubistid näitasid korraga mitut vaatepunkti ning abstraktsioon muutis värvi, kuju ja rütmi iseseisvateks teemadeks.

Teoseid võrreldes jälgi **järjepidevust ja muutust**: milline traditsioon püsib? Mis muutus tehnikas, publikus, teemas või eesmärgis? Kunstivool muutub selgemaks, kui näed seda vastusena varasemale kunstile ja oma ajastu ühiskonnale.""",
                        """# Nuo Renesanso iki modernizmo

Renesanso menininkai atgaivino antikos idėjas ir plėtojo linijinę perspektyvą, atidų stebėjimą bei naujas mecenatystės formas. Baroko menas sustiprino judesį, dramą ir kontrastą. XIX amžiuje industrializacija, fotografija, miestai ir politiniai pokyčiai metė iššūkį paveldėtoms taisyklėms.

Modernizmas nėra vienas stilius. Impresionistai tyrinėjo kintančią šviesą, kubistai vienu metu rodė kelis požiūrio taškus, o abstrakcija spalvą, formą ir ritmą pavertė savarankiškomis temomis.

Lygindami kūrinius sekite **tęstinumą ir pokytį**: kokia tradicija išlieka? Kas pasikeitė technikoje, auditorijoje, temoje ar paskirtyje? Kryptį lengviau suprasti kaip atsaką į ankstesnį meną ir savo laikotarpio visuomenę.""",
                        """# Del Renacimiento al modernismo

Los artistas renacentistas recuperaron ideas clásicas y desarrollaron la perspectiva lineal, la observación atenta y nuevas formas de mecenazgo. El Barroco intensificó el movimiento, el drama y el contraste. En el siglo XIX, la industrialización, la fotografía, las ciudades y el cambio político cuestionaron las reglas heredadas.

El modernismo no es un solo estilo. Los impresionistas estudiaron la luz cambiante; los cubistas mostraron varios puntos de vista a la vez; la abstracción convirtió el color, la forma y el ritmo en temas por sí mismos.

Al comparar obras, sigue la **continuidad y el cambio**: ¿qué tradición permanece? ¿Qué cambió en técnica, público, tema o propósito? Un movimiento se entiende mejor como respuesta al arte anterior y a su propio mundo social.""",
                    ),
                    "xp_reward": 30,
                    "duration_min": 20,
                },
            ],
        }],
    },
    {
        "title": _t("Music History", "Muusikaajalugu", "Muzikos istorija", "Historia de la música"),
        "slug": "music-history",
        "description": _t("Follow how musical ideas, instruments, notation, and listening cultures changed from early traditions to recorded music.", "Jälgi, kuidas muusikalised ideed, pillid, noodikiri ja kuulamiskultuur muutusid varastest traditsioonidest salvestatud muusikani.", "Sekite, kaip muzikinės idėjos, instrumentai, notacija ir klausymosi kultūra keitėsi nuo ankstyvųjų tradicijų iki įrašytos muzikos.", "Sigue la evolución de las ideas musicales, los instrumentos, la notación y las culturas de escucha desde las primeras tradiciones hasta la música grabada."),
        "category": _t("Music History", "Muusikaajalugu", "Muzikos istorija", "Historia de la música"),
        "difficulty": "beginner",
        "is_published": True,
        "modules": [{
            "title": _t("Listening Through Time", "Kuulamine läbi aja", "Klausymasis per laiką", "Escuchar a través del tiempo"),
            "lessons": [
                {
                    "title": _t("Oral Tradition, Notation, and the Baroque", "Suuline pärimus, noodikiri ja barokk", "Žodinė tradicija, notacija ir barokas", "Tradición oral, notación y Barroco"),
                    "content_md": _t(
                        """# Oral Tradition, Notation, and the Baroque

Music existed before writing. Communities carried songs through memory, repetition, and participation. Notation later made some music easier to preserve, coordinate, and transmit, but it never captured every detail of performance.

Medieval European traditions developed chant and polyphony—several independent lines sounding together. Renaissance composers refined vocal balance and imitation. Baroque music favoured contrast, ornament, basso continuo, and emerging major–minor harmony; opera joined music, theatre, and spectacle.

Historical listening asks who performed, where, for whom, and with which technologies. A score is one source; instruments, venues, patronage, and oral practice also shape what music meant.""",
                        """# Suuline pärimus, noodikiri ja barokk

Muusika oli olemas enne kirja. Kogukonnad kandsid laule edasi mälu, korduse ja osalemise kaudu. Noodikiri muutis osa muusikast lihtsamini säilitatavaks, koordineeritavaks ja edasiantavaks, kuid ei talletanud kunagi kõiki esituse üksikasju.

Keskaegses Euroopas arenesid kirikulaul ja polüfoonia ehk mitu iseseisvat samaaegset häält. Renessansil täiustati vokaalset tasakaalu ja imitatsiooni. Barokk eelistas kontrasti, kaunistusi, basso continuo't ja kujunevat mažoor-minoor-harmooniat; ooper ühendas muusika, teatri ja vaatemängu.

Ajalooline kuulamine küsib, kes esitas, kus, kellele ja milliste tehnoloogiatega. Partituur on vaid üks allikas; tähendust kujundavad ka pillid, ruumid, metseenlus ja suuline praktika.""",
                        """# Žodinė tradicija, notacija ir barokas

Muzika egzistavo dar iki rašto. Bendruomenės perdavė dainas per atmintį, kartojimą ir dalyvavimą. Vėliau notacija padėjo kai kurią muziką išsaugoti, koordinuoti ir perduoti, tačiau niekada neužfiksavo visų atlikimo detalių.

Viduramžių Europoje plėtojosi giedojimas ir polifonija – keli savarankiški vienu metu skambantys balsai. Renesanso kompozitoriai tobulino vokalinę pusiausvyrą ir imitaciją. Barokas mėgo kontrastą, ornamentiką, basso continuo ir besiformuojančią mažoro–minoro harmoniją; opera sujungė muziką, teatrą ir reginį.

Istorinis klausymasis klausia, kas, kur, kam ir kokiomis technologijomis atliko muziką. Partitūra yra tik vienas šaltinis; prasmę taip pat formuoja instrumentai, erdvės, mecenatystė ir žodinė praktika.""",
                        """# Tradición oral, notación y Barroco

La música existía antes de la escritura. Las comunidades transmitían canciones mediante memoria, repetición y participación. La notación permitió conservar, coordinar y transmitir parte de la música, pero nunca captó todos los detalles de una interpretación.

Las tradiciones medievales europeas desarrollaron el canto y la polifonía: varias líneas independientes sonando juntas. El Renacimiento refinó el equilibrio vocal y la imitación. El Barroco favoreció el contraste, el ornamento, el bajo continuo y la naciente armonía mayor-menor; la ópera unió música, teatro y espectáculo.

La escucha histórica pregunta quién interpretaba, dónde, para quién y con qué tecnologías. Una partitura es una fuente; los instrumentos, espacios, mecenas y prácticas orales también construyen el significado.""",
                    ),
                    "xp_reward": 25,
                    "duration_min": 18,
                    "quiz": {
                        "title": _t("Early Music History Quiz", "Varase muusikaajaloo viktoriin", "Ankstyvosios muzikos istorijos testas", "Cuestionario de historia musical temprana"),
                        "pass_threshold": 60,
                        "xp_reward": 30,
                        "questions": [
                            {
                                "question_text": _t("What is polyphony?", "Mis on polüfoonia?", "Kas yra polifonija?", "¿Qué es la polifonía?"),
                                "options": _t(["Several independent musical lines together", "Music without rhythm", "A single drum", "A recording method"], ["Mitu iseseisvat muusikalist liini koos", "Rütmita muusika", "Üks trumm", "Salvestusmeetod"], ["Kelios savarankiškos muzikinės linijos kartu", "Muzika be ritmo", "Vienas būgnas", "Įrašymo būdas"], ["Varias líneas musicales independientes juntas", "Música sin ritmo", "Un solo tambor", "Un método de grabación"]),
                                "correct_answer": _t("Several independent musical lines together", "Mitu iseseisvat muusikalist liini koos", "Kelios savarankiškos muzikinės linijos kartu", "Varias líneas musicales independientes juntas"),
                                "explanation": _t("Polyphony combines distinct simultaneous melodic lines.", "Polüfoonia ühendab erinevad samaaegsed meloodialiinid.", "Polifonija sujungia skirtingas vienu metu skambančias melodines linijas.", "La polifonía combina líneas melódicas distintas y simultáneas."),
                            },
                            {
                                "question_text": _t("Which genre joined music, theatre, and spectacle in the Baroque era?", "Milline žanr ühendas barokiajal muusika, teatri ja vaatemängu?", "Kuris žanras baroko laikais sujungė muziką, teatrą ir reginį?", "¿Qué género unió música, teatro y espectáculo durante el Barroco?"),
                                "options": _t(["Opera", "Photography", "Cubism", "Podcast"], ["Ooper", "Fotograafia", "Kubism", "Taskuhääling"], ["Opera", "Fotografija", "Kubizmas", "Tinklalaidė"], ["Ópera", "Fotografía", "Cubismo", "Pódcast"]),
                                "correct_answer": _t("Opera", "Ooper", "Opera", "Ópera"),
                                "explanation": _t("Opera combines sung drama, instruments, staging, and visual design.", "Ooper ühendab lauldud draama, pillid, lavastuse ja visuaalse kujunduse.", "Opera jungia dainuojamą dramą, instrumentus, sceninį veiksmą ir vaizdinį dizainą.", "La ópera combina drama cantado, instrumentos, puesta en escena y diseño visual."),
                            },
                        ],
                    },
                },
                {
                    "title": _t("Classical Traditions to Recorded Music", "Klassikatraditsioonidest salvestatud muusikani", "Nuo klasikinės tradicijos iki įrašytos muzikos", "De la tradición clásica a la música grabada"),
                    "content_md": _t(
                        """# Classical Traditions to Recorded Music

The Classical era valued clarity, balance, and intelligible form. Romantic composers expanded orchestras and expressive range, often linking music with literature, nature, nationalism, or personal feeling.

The twentieth century multiplied possibilities: modernist experiments, jazz improvisation, blues-derived popular music, electronic sound, film scoring, and traditions exchanged across global networks. Recording changed music itself—listeners could replay performances, artists could compose in the studio, and styles travelled quickly.

Avoid treating history as a single ladder of progress. Musical cultures overlap, borrow, resist, and continue alongside one another. Ask whose music was documented, whose was excluded, and how media changed what audiences could hear.""",
                        """# Klassikatraditsioonidest salvestatud muusikani

Klassitsism väärtustas selgust, tasakaalu ja arusaadavat vormi. Romantilised heliloojad suurendasid orkestreid ja väljendusulatust ning sidusid muusikat kirjanduse, looduse, rahvusluse või isiklike tunnetega.

20. sajand mitmekordistas võimalusi: modernistlikud katsed, džässi improvisatsioon, bluusist lähtuv levimuusika, elektrooniline heli, filmimuusika ja globaalsetes võrgustikes kohtuvad traditsioonid. Salvestamine muutis muusikat ennast — esitusi sai korrata, stuudios komponeerida ja stiilid liikusid kiiresti.

Ära käsitle ajalugu ühe arenguredelina. Muusikakultuurid kattuvad, laenavad, vastanduvad ja jätkuvad kõrvuti. Küsi, kelle muusika dokumenteeriti, kes jäeti välja ja kuidas meedia muutis kuuldavat.""",
                        """# Nuo klasikinės tradicijos iki įrašytos muzikos

Klasicizmo epocha vertino aiškumą, pusiausvyrą ir suprantamą formą. Romantizmo kompozitoriai išplėtė orkestrus ir išraiškos ribas, dažnai siedami muziką su literatūra, gamta, nacionalizmu ar asmeniniais jausmais.

XX amžius padaugino galimybes: modernistiniai eksperimentai, džiazo improvizacija, iš bliuzo kilusi populiarioji muzika, elektroninis garsas, kino muzika ir tradicijų mainai pasauliniuose tinkluose. Įrašai pakeitė pačią muziką – klausytojai galėjo kartoti atlikimus, kūrėjai komponuoti studijoje, o stiliai greitai plito.

Nelaikykite istorijos vienomis pažangos kopėčiomis. Muzikinės kultūros persidengia, skolinasi, priešinasi ir gyvuoja greta. Klauskite, kieno muzika buvo dokumentuota, kas liko nuošalyje ir kaip medijos pakeitė girdimą pasaulį.""",
                        """# De la tradición clásica a la música grabada

La era clásica valoró claridad, equilibrio y formas comprensibles. Los compositores románticos ampliaron la orquesta y el rango expresivo, vinculando a menudo la música con literatura, naturaleza, nacionalismo o sentimiento personal.

El siglo XX multiplicó las posibilidades: experimentos modernistas, improvisación de jazz, música popular derivada del blues, sonido electrónico, bandas sonoras e intercambio entre tradiciones globales. La grabación cambió la música: permitió repetir interpretaciones, componer en el estudio y difundir estilos con rapidez.

No trates la historia como una sola escalera de progreso. Las culturas musicales se superponen, toman prestado, resisten y continúan en paralelo. Pregunta qué música se documentó, cuál se excluyó y cómo los medios cambiaron lo que el público podía oír.""",
                    ),
                    "xp_reward": 30,
                    "duration_min": 20,
                },
            ],
        }],
    },
    {
        "title": _t("Art", "Kunst", "Menas", "Arte"),
        "slug": "art-principles",
        "description": _t("Understand the visual elements and composition principles used to analyse and plan artworks—no drawing tools required.", "Mõista kunstiteoste analüüsimisel ja kavandamisel kasutatavaid visuaalseid elemente ning kompositsioonipõhimõtteid — joonistusvahendeid pole vaja.", "Supraskite vizualius elementus ir kompozicijos principus, naudojamus meno kūriniams analizuoti ir planuoti – piešimo priemonių nereikia.", "Comprende los elementos visuales y principios de composición usados para analizar y planificar obras, sin necesidad de herramientas de dibujo."),
        "category": _t("Art", "Kunst", "Menas", "Arte"),
        "difficulty": "beginner",
        "is_published": True,
        "modules": [{
            "title": _t("Visual Language", "Visuaalne keel", "Vizualinė kalba", "Lenguaje visual"),
            "lessons": [
                {
                    "title": _t("The Elements of Art", "Kunsti elemendid", "Meno elementai", "Los elementos del arte"),
                    "content_md": _t(
                        """# The Elements of Art

The elements are the basic ingredients of visual work:

- **Line** directs movement and defines edges.
- **Shape** is flat; **form** suggests three dimensions.
- **Colour** combines hue, value, and intensity.
- **Value** is the range from light to dark.
- **Texture** may be physical or visually implied.
- **Space** describes depth, distance, and the areas around forms.

Analysis begins with evidence. Instead of saying “it feels dramatic,” identify the steep diagonals, dark values, compressed space, or intense colour that create that effect. These principles can be learned through observation and planning; drawing practice is not required in this course.""",
                        """# Kunsti elemendid

Elemendid on visuaalse teose põhikoostisosad:

- **Joon** suunab liikumist ja määratleb servi.
- **Kujund** on tasapinnaline; **vorm** viitab kolmele mõõtmele.
- **Värv** ühendab värvitooni, heleduse ja intensiivsuse.
- **Tonaalsus** ulatub heledast tumedani.
- **Tekstuur** võib olla füüsiline või visuaalselt aimatav.
- **Ruum** kirjeldab sügavust, kaugust ja vormide ümbrust.

Analüüs algab tõenditest. Selle asemel et öelda „see tundub dramaatiline“, nimeta järsud diagonaalid, tumedad toonid, kokkusurutud ruum või intensiivne värv, mis mõju loovad. Neid põhimõtteid saab õppida vaatluse ja kavandamise kaudu; joonistamist see kursus ei eelda.""",
                        """# Meno elementai

Elementai yra pagrindinės vizualaus kūrinio sudedamosios dalys:

- **Linija** nukreipia judesį ir apibrėžia kraštus.
- **Figūra** yra plokščia, o **forma** perteikia tris matmenis.
- **Spalva** apima atspalvį, šviesumą ir intensyvumą.
- **Tonas** driekiasi nuo šviesaus iki tamsaus.
- **Tekstūra** gali būti fizinė arba vizualiai numanoma.
- **Erdvė** apibūdina gylį, atstumą ir plotus aplink formas.

Analizė prasideda nuo įrodymų. Užuot sakę „atrodo dramatiška“, įvardykite staigias įstrižaines, tamsius tonus, suspaustą erdvę ar intensyvią spalvą, kurios kuria šį poveikį. Šiuos principus galima išmokti stebint ir planuojant; piešimo praktikos šiame kurse nereikia.""",
                        """# Los elementos del arte

Los elementos son los ingredientes básicos de una obra visual:

- La **línea** dirige el movimiento y define bordes.
- La **figura** es plana; la **forma** sugiere tres dimensiones.
- El **color** combina matiz, valor e intensidad.
- El **valor** abarca de claro a oscuro.
- La **textura** puede ser física o visualmente sugerida.
- El **espacio** describe profundidad, distancia y áreas alrededor de las formas.

El análisis empieza con evidencias. En vez de decir «parece dramático», identifica diagonales pronunciadas, valores oscuros, espacio comprimido o color intenso. Estos principios se aprenden observando y planificando; este curso no exige práctica de dibujo.""",
                    ),
                    "xp_reward": 20,
                    "duration_min": 15,
                    "quiz": {
                        "title": _t("Elements of Art Quiz", "Kunstielementide viktoriin", "Meno elementų testas", "Cuestionario de elementos del arte"),
                        "pass_threshold": 60,
                        "xp_reward": 25,
                        "questions": [
                            {
                                "question_text": _t("Which element describes the range from light to dark?", "Milline element kirjeldab vahemikku heledast tumedani?", "Kuris elementas apibūdina diapazoną nuo šviesaus iki tamsaus?", "¿Qué elemento describe el rango de claro a oscuro?"),
                                "options": _t(["Value", "Line", "Space", "Texture"], ["Tonaalsus", "Joon", "Ruum", "Tekstuur"], ["Tonas", "Linija", "Erdvė", "Tekstūra"], ["Valor", "Línea", "Espacio", "Textura"]),
                                "correct_answer": _t("Value", "Tonaalsus", "Tonas", "Valor"),
                                "explanation": _t("Value is the relative lightness or darkness of a colour or tone.", "Tonaalsus näitab värvi või tooni suhtelist heledust või tumedust.", "Tonas nusako santykinį spalvos ar atspalvio šviesumą arba tamsumą.", "El valor es la claridad u oscuridad relativa de un color o tono."),
                            },
                            {
                                "question_text": _t("What is the difference between shape and form?", "Mis vahe on kujundil ja vormil?", "Kuo skiriasi figūra ir forma?", "¿Cuál es la diferencia entre figura y forma?"),
                                "options": _t(["Shape is flat; form suggests three dimensions", "Form is always red", "Shape is sound", "There is no difference"], ["Kujund on tasapinnaline; vorm viitab kolmele mõõtmele", "Vorm on alati punane", "Kujund on heli", "Erinevust pole"], ["Figūra yra plokščia, forma perteikia tris matmenis", "Forma visada raudona", "Figūra yra garsas", "Skirtumo nėra"], ["La figura es plana; la forma sugiere tres dimensiones", "La forma siempre es roja", "La figura es sonido", "No hay diferencia"]),
                                "correct_answer": _t("Shape is flat; form suggests three dimensions", "Kujund on tasapinnaline; vorm viitab kolmele mõõtmele", "Figūra yra plokščia, forma perteikia tris matmenis", "La figura es plana; la forma sugiere tres dimensiones"),
                                "explanation": _t("Shape has height and width; form also suggests depth.", "Kujundil on kõrgus ja laius; vorm viitab ka sügavusele.", "Figūra turi aukštį ir plotį, o forma perteikia ir gylį.", "La figura tiene alto y ancho; la forma también sugiere profundidad."),
                            },
                        ],
                    },
                },
                {
                    "title": _t("Composition and Visual Meaning", "Kompositsioon ja visuaalne tähendus", "Kompozicija ir vizualinė prasmė", "Composición y significado visual"),
                    "content_md": _t(
                        """# Composition and Visual Meaning

Composition is how visual elements are organised. **Balance** distributes visual weight; it may be symmetrical, asymmetrical, or radial. **Contrast** makes differences noticeable. **Emphasis** creates a focal point. **Rhythm** and **pattern** guide the eye through repetition. **Proportion** compares sizes, while **unity** makes parts feel related.

Every choice affects meaning. A centred, symmetrical image may feel stable; an off-centre subject with strong diagonals may feel active or uncertain. Empty space can isolate a figure or create calm.

To analyse a composition, trace where your eye goes first, second, and third. Then name the element or principle responsible. This turns a personal reaction into a supported visual argument.""",
                        """# Kompositsioon ja visuaalne tähendus

Kompositsioon tähendab visuaalsete elementide korraldust. **Tasakaal** jaotab visuaalset raskust ning võib olla sümmeetriline, asümmeetriline või radiaalne. **Kontrast** muudab erinevused märgatavaks. **Rõhuasetus** loob fookuspunkti. **Rütm** ja **muster** juhivad korduse abil pilku. **Proportsioon** võrdleb suurusi ning **ühtsus** seob osad tervikuks.

Iga valik mõjutab tähendust. Keskne sümmeetriline kujutis võib tunduda stabiilne; keskpunktist eemal paiknev objekt ja tugevad diagonaalid võivad mõjuda aktiivselt või ebakindlalt. Tühi ruum võib figuuri isoleerida või luua rahu.

Analüüsides jälgi, kuhu pilk liigub esimesena, teisena ja kolmandana. Seejärel nimeta vastutav element või põhimõte. Nii muutub isiklik reaktsioon põhjendatud visuaalseks väiteks.""",
                        """# Kompozicija ir vizualinė prasmė

Kompozicija yra vizualių elementų išdėstymas. **Pusiausvyra** paskirsto vizualų svorį ir gali būti simetriška, asimetriška ar radialinė. **Kontrastas** išryškina skirtumus. **Akcentas** sukuria dėmesio centrą. **Ritmas** ir **raštas** kartojimu veda žvilgsnį. **Proporcija** lygina dydžius, o **vienovė** susieja dalis.

Kiekvienas pasirinkimas keičia prasmę. Centruotas simetriškas vaizdas gali atrodyti stabilus; ne centre esantis objektas su ryškiomis įstrižainėmis – aktyvus ar neramus. Tuščia erdvė gali izoliuoti figūrą arba suteikti ramybės.

Analizuodami sekite, kur žvilgsnis krypsta pirmiausia, antra ir trečia. Tada įvardykite tai lemiantį elementą ar principą. Taip asmeninė reakcija tampa pagrįstu vizualiu argumentu.""",
                        """# Composición y significado visual

La composición organiza los elementos visuales. El **equilibrio** distribuye el peso visual y puede ser simétrico, asimétrico o radial. El **contraste** hace visibles las diferencias. El **énfasis** crea un punto focal. El **ritmo** y el **patrón** guían la mirada mediante repetición. La **proporción** compara tamaños y la **unidad** relaciona las partes.

Cada decisión afecta al significado. Una imagen centrada y simétrica puede parecer estable; un sujeto descentrado con diagonales fuertes puede parecer activo o incierto. El espacio vacío puede aislar una figura o crear calma.

Para analizar una composición, sigue hacia dónde va tu mirada en primer, segundo y tercer lugar. Después nombra el elemento o principio responsable. Así una reacción personal se convierte en un argumento visual fundamentado.""",
                    ),
                    "xp_reward": 25,
                    "duration_min": 18,
                },
            ],
        }],
    },
    {
        "title": _t("Music", "Muusika", "Muzika", "Música"),
        "slug": "music-principles",
        "description": _t("Learn the concepts behind rhythm, melody, harmony, form, texture, timbre, and dynamics—without requiring singing or an instrument.", "Õpi rütmi, meloodia, harmoonia, vormi, faktuuri, tämbri ja dünaamika mõisteid ilma laulmise või pillimängu nõudeta.", "Sužinokite ritmo, melodijos, harmonijos, formos, faktūros, tembro ir dinamikos sąvokas – nereikia dainuoti ar groti instrumentu.", "Aprende los conceptos de ritmo, melodía, armonía, forma, textura, timbre y dinámica sin necesidad de cantar ni tocar un instrumento."),
        "category": _t("Music", "Muusika", "Muzika", "Música"),
        "difficulty": "beginner",
        "is_published": True,
        "modules": [{
            "title": _t("How Music Works", "Kuidas muusika toimib", "Kaip veikia muzika", "Cómo funciona la música"),
            "lessons": [
                {
                    "title": _t("Rhythm, Melody, and Harmony", "Rütm, meloodia ja harmoonia", "Ritmas, melodija ir harmonija", "Ritmo, melodía y armonía"),
                    "content_md": _t(
                        """# Rhythm, Melody, and Harmony

**Beat** is the recurring pulse; **metre** groups beats; **rhythm** is the pattern of durations and accents across that pulse. Tempo tells us how quickly the beat moves.

**Pitch** describes how high or low a sound seems. A **melody** is a meaningful succession of pitches and rhythms. Its contour may rise, fall, repeat, or leap. A short recognisable idea is often called a motif.

**Harmony** concerns notes sounding together and how chords move. Consonance can feel settled and dissonance tense, but those effects depend on style and culture. You can analyse all three layers by attentive listening: tap the pulse, trace the tune, and notice moments of stability or tension. No singing or instrument is required.""",
                        """# Rütm, meloodia ja harmoonia

**Pulss** on korduv löök, **meetrum** rühmitab lööke ning **rütm** on kestuste ja rõhkude muster selle pulsi kohal. Tempo näitab, kui kiiresti pulss liigub.

**Helikõrgus** kirjeldab, kui kõrge või madal heli tundub. **Meloodia** on tähenduslik helikõrguste ja rütmide järgnevus. Selle kontuur võib tõusta, langeda, korduda või hüpata. Lühikest äratuntavat ideed nimetatakse sageli motiiviks.

**Harmoonia** käsitleb koos kõlavaid helisid ja akordide liikumist. Konsonants võib tunduda rahulik ja dissonants pingeline, kuid mõju sõltub stiilist ja kultuurist. Kuulates saad analüüsida kõiki kihte: koputa pulssi, jälgi meloodiat ning märka stabiilsust ja pinget. Laulmist ega pilli pole vaja.""",
                        """# Ritmas, melodija ir harmonija

**Pulsas** yra pasikartojantis dūžis, **metras** grupuoja dūžius, o **ritmas** – trukmių ir akcentų raštas virš pulso. Tempas nusako pulso greitį.

**Garso aukštis** apibūdina, kiek garsas atrodo aukštas ar žemas. **Melodija** yra prasminga garsų aukščių ir ritmų seka. Jos kontūras gali kilti, leistis, kartotis ar šokinėti. Trumpa atpažįstama idėja dažnai vadinama motyvu.

**Harmonija** apima kartu skambančias natas ir akordų judėjimą. Konsonansas gali skambėti ramiai, disonansas – įtemptai, tačiau poveikis priklauso nuo stiliaus ir kultūros. Klausydamiesi galite analizuoti visus sluoksnius: muškite pulsą, sekite melodiją ir pastebėkite stabilumą ar įtampą. Dainuoti ar groti instrumentu nereikia.""",
                        """# Ritmo, melodía y armonía

El **pulso** es la pulsación recurrente; el **compás** agrupa pulsos; el **ritmo** organiza duraciones y acentos sobre ese pulso. El tempo indica la velocidad.

La **altura** describe si un sonido parece agudo o grave. Una **melodía** es una sucesión significativa de alturas y ritmos. Su contorno puede subir, bajar, repetirse o saltar. Una idea breve y reconocible suele llamarse motivo.

La **armonía** trata las notas que suenan juntas y el movimiento de los acordes. La consonancia puede parecer estable y la disonancia tensa, aunque depende del estilo y la cultura. Puedes analizar las tres capas escuchando: marca el pulso, sigue la melodía y nota estabilidad o tensión. No hace falta cantar ni tocar un instrumento.""",
                    ),
                    "xp_reward": 20,
                    "duration_min": 15,
                    "quiz": {
                        "title": _t("Music Building Blocks Quiz", "Muusika ehituskivide viktoriin", "Muzikos pagrindų testas", "Cuestionario de componentes musicales"),
                        "pass_threshold": 60,
                        "xp_reward": 25,
                        "questions": [
                            {
                                "question_text": _t("What does metre do?", "Mida teeb meetrum?", "Ką daro metras?", "¿Qué hace el compás?"),
                                "options": _t(["Groups beats", "Changes timbre", "Names an instrument", "Removes rhythm"], ["Rühmitab lööke", "Muudab tämbrit", "Nimetab pilli", "Eemaldab rütmi"], ["Grupuoja dūžius", "Keičia tembrą", "Įvardija instrumentą", "Pašalina ritmą"], ["Agrupa pulsos", "Cambia el timbre", "Nombra un instrumento", "Elimina el ritmo"]),
                                "correct_answer": _t("Groups beats", "Rühmitab lööke", "Grupuoja dūžius", "Agrupa pulsos"),
                                "explanation": _t("Metre organises recurring beats into recognisable groups.", "Meetrum korraldab korduvad löögid äratuntavateks rühmadeks.", "Metras pasikartojančius dūžius suskirsto į atpažįstamas grupes.", "El compás organiza pulsos recurrentes en grupos reconocibles."),
                            },
                            {
                                "question_text": _t("What is a melody?", "Mis on meloodia?", "Kas yra melodija?", "¿Qué es una melodía?"),
                                "options": _t(["A meaningful succession of pitches and rhythms", "Only loudness", "The material of an instrument", "A type of venue"], ["Tähenduslik helikõrguste ja rütmide järgnevus", "Ainult valjus", "Pilli materjal", "Kontserdipaiga liik"], ["Prasminga garsų aukščių ir ritmų seka", "Tik garsumas", "Instrumento medžiaga", "Erdvės tipas"], ["Una sucesión significativa de alturas y ritmos", "Solo volumen", "El material de un instrumento", "Un tipo de sala"]),
                                "correct_answer": _t("A meaningful succession of pitches and rhythms", "Tähenduslik helikõrguste ja rütmide järgnevus", "Prasminga garsų aukščių ir ritmų seka", "Una sucesión significativa de alturas y ritmos"),
                                "explanation": _t("Melody combines pitch and rhythm into a line listeners can follow.", "Meloodia ühendab helikõrguse ja rütmi kuulaja jälgitavaks liiniks.", "Melodija sujungia garso aukštį ir ritmą į klausytojui sekamą liniją.", "La melodía combina altura y ritmo en una línea que el oyente puede seguir."),
                            },
                        ],
                    },
                },
                {
                    "title": _t("Form, Texture, Timbre, and Dynamics", "Vorm, faktuur, tämber ja dünaamika", "Forma, faktūra, tembras ir dinamika", "Forma, textura, timbre y dinámica"),
                    "content_md": _t(
                        """# Form, Texture, Timbre, and Dynamics

**Form** is the large-scale plan of music. Repetition creates recognition, contrast brings new material, and return creates orientation. Labels such as ABA, verse–chorus, or theme and variations map that plan.

**Texture** describes how musical layers relate: monophonic (one line), homophonic (melody with support), or polyphonic (independent lines). **Timbre** is sound colour—the quality distinguishing a violin from a flute on the same note. **Dynamics** describe levels and changes of loudness.

Create a listening map with timestamps. Mark sections, returns, changes in layer, new sound colours, and dynamic peaks. This principles course develops informed listening and vocabulary; it does not yet teach instrumental or vocal technique.""",
                        """# Vorm, faktuur, tämber ja dünaamika

**Vorm** on muusika suur plaan. Kordus loob äratundmise, kontrast toob uue materjali ning tagasitulek aitab orienteeruda. Tähised nagu ABA, salm–refrään või teema variatsioonidega kaardistavad seda plaani.

**Faktuur** kirjeldab muusikakihtide suhet: monofooniline (üks liin), homofooniline (meloodia koos saatega) või polüfooniline (iseseisvad liinid). **Tämber** on helivärv, mis eristab sama nooti mängivat viiulit ja flööti. **Dünaamika** kirjeldab valjuse tasemeid ja muutusi.

Koosta ajatemplitega kuulamiskaart. Märgi osad, tagasitulekud, kihtide muutused, uued tämbrid ja dünaamilised tipud. Kursus arendab teadlikku kuulamist ja sõnavara; pilli- ega hääletehnikat see veel ei õpeta.""",
                        """# Forma, faktūra, tembras ir dinamika

**Forma** yra didysis muzikos planas. Kartojimas padeda atpažinti, kontrastas pateikia naują medžiagą, o sugrįžimas padeda orientuotis. Tokie ženklai kaip ABA, posmas–priedainis ar tema su variacijomis žymi šį planą.

**Faktūra** apibūdina muzikinių sluoksnių ryšį: monofoninė (viena linija), homofoninė (melodija su pritarimu) arba polifoninė (savarankiškos linijos). **Tembras** yra garso spalva, skirianti smuiką nuo fleitos, kai grojama ta pati nata. **Dinamika** nusako garsumo lygius ir pokyčius.

Sukurkite klausymosi žemėlapį su laiko žymomis. Pažymėkite dalis, sugrįžimus, sluoksnių pokyčius, naujas garso spalvas ir dinamines viršūnes. Kursas ugdo sąmoningą klausymąsi ir žodyną; instrumentinės ar vokalinės technikos dar nemoko.""",
                        """# Forma, textura, timbre y dinámica

La **forma** es el plan general de la música. La repetición crea reconocimiento, el contraste aporta material nuevo y el retorno orienta. Etiquetas como ABA, estrofa–estribillo o tema y variaciones representan ese plan.

La **textura** describe la relación entre capas: monofónica (una línea), homofónica (melodía con apoyo) o polifónica (líneas independientes). El **timbre** es el color sonoro que distingue un violín de una flauta en la misma nota. La **dinámica** describe niveles y cambios de volumen.

Crea un mapa de escucha con marcas de tiempo. Señala secciones, retornos, cambios de capa, nuevos colores y puntos dinámicos máximos. Este curso desarrolla escucha informada y vocabulario; todavía no enseña técnica instrumental ni vocal.""",
                    ),
                    "xp_reward": 25,
                    "duration_min": 18,
                },
            ],
        }],
    },
]


def _english(value):
    if isinstance(value, dict):
        if set(value) == set(LANGUAGES):
            return deepcopy(value["en"])
        return {key: _english(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_english(item) for item in value]
    return deepcopy(value)


def _translation(source, record, fields):
    return {
        "source": source,
        **{
            lang: {field: deepcopy(record[field][lang]) for field in fields}
            for lang in LANGUAGES
            if lang != "en"
        },
    }


def _build_translations():
    result = {"courses": {}, "modules": {}, "lessons": {}, "quizzes": {}, "quiz_questions": {}}
    for course in CATALOG:
        slug = course["slug"]
        result["courses"][slug] = _translation(course["title"]["en"], course, ("title", "description", "category"))
        for module_index, module in enumerate(course["modules"]):
            module_key = f"{slug}:module:{module_index}"
            result["modules"][module_key] = _translation(module["title"]["en"], module, ("title",))
            for lesson_index, lesson in enumerate(module["lessons"]):
                lesson_key = f"{slug}:lesson:{module_index}:{lesson_index}"
                result["lessons"][lesson_key] = _translation(lesson["title"]["en"], lesson, ("title", "content_md"))
                quiz = lesson.get("quiz")
                if not quiz:
                    continue
                quiz_key = f"{lesson_key}:quiz"
                result["quizzes"][quiz_key] = _translation(quiz["title"]["en"], quiz, ("title",))
                for question_index, question in enumerate(quiz["questions"]):
                    question_key = f"{quiz_key}:question:{question_index}"
                    result["quiz_questions"][question_key] = _translation(
                        question["question_text"]["en"], question,
                        ("question_text", "options", "correct_answer", "explanation"),
                    )
    return result


ART_COURSES = _english(CATALOG)
ART_TRANSLATIONS = _build_translations()


def seed_art_courses(conn, schema: str) -> list[dict]:
    """Idempotently install the four protected Art and Music courses."""
    owner_id = conn.execute(sa.text(f"""
        SELECT id FROM {schema}.users
        ORDER BY CASE
            WHEN lower(email) = 'kaljuvee@gmail.com' THEN 0
            WHEN lower(email) = 'instructor@fastlms.dev' THEN 1
            ELSE 2
        END, id
        LIMIT 1
    """)).scalar()
    seeded = []
    for course_data in ART_COURSES:
        course = conn.execute(sa.text(f"""
            INSERT INTO {schema}.courses
                (title, slug, description, category, difficulty, is_published,
                 instructor_id, is_default)
            VALUES (:title, :slug, :description, :category, :difficulty, true,
                    :owner, true)
            ON CONFLICT (slug) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                category = EXCLUDED.category,
                difficulty = EXCLUDED.difficulty,
                is_published = true,
                is_default = true,
                instructor_id = COALESCE(EXCLUDED.instructor_id, {schema}.courses.instructor_id)
            RETURNING *
        """), {
            **{key: course_data[key] for key in (
                "title", "slug", "description", "category", "difficulty"
            )},
            "owner": owner_id,
        }).mappings().one()

        for module_index, module_data in enumerate(course_data["modules"]):
            module_id = conn.execute(sa.text(f"""
                SELECT id FROM {schema}.modules
                WHERE course_id = :course AND title = :title
                ORDER BY id LIMIT 1
            """), {
                "course": course["id"], "title": module_data["title"]
            }).scalar()
            if module_id:
                conn.execute(sa.text(f"""
                    UPDATE {schema}.modules SET order_idx = :order_idx WHERE id = :id
                """), {"order_idx": module_index, "id": module_id})
            else:
                module_id = conn.execute(sa.text(f"""
                    INSERT INTO {schema}.modules (course_id, title, order_idx)
                    VALUES (:course, :title, :order_idx) RETURNING id
                """), {
                    "course": course["id"], "title": module_data["title"],
                    "order_idx": module_index,
                }).scalar_one()

            for lesson_index, lesson_data in enumerate(module_data["lessons"]):
                lesson_id = conn.execute(sa.text(f"""
                    SELECT id FROM {schema}.lessons
                    WHERE module_id = :module AND title = :title
                    ORDER BY id LIMIT 1
                """), {
                    "module": module_id, "title": lesson_data["title"]
                }).scalar()
                lesson_params = {
                    "module": module_id,
                    "title": lesson_data["title"],
                    "content": lesson_data.get("content_md", ""),
                    "duration": lesson_data.get("duration_min", 10),
                    "xp": lesson_data.get("xp_reward", 25),
                    "order_idx": lesson_index,
                }
                if lesson_id:
                    conn.execute(sa.text(f"""
                        UPDATE {schema}.lessons SET
                            content_md = :content,
                            duration_min = :duration,
                            xp_reward = :xp,
                            order_idx = :order_idx
                        WHERE id = :id
                    """), {**lesson_params, "id": lesson_id})
                else:
                    lesson_id = conn.execute(sa.text(f"""
                        INSERT INTO {schema}.lessons
                            (module_id, title, content_md, duration_min, xp_reward, order_idx)
                        VALUES (:module, :title, :content, :duration, :xp, :order_idx)
                        RETURNING id
                    """), lesson_params).scalar_one()

                quiz_data = lesson_data.get("quiz")
                if not quiz_data:
                    continue
                quiz_id = conn.execute(sa.text(f"""
                    SELECT id FROM {schema}.quizzes
                    WHERE lesson_id = :lesson ORDER BY id LIMIT 1
                """), {"lesson": lesson_id}).scalar()
                quiz_params = {
                    "lesson": lesson_id,
                    "title": quiz_data["title"],
                    "threshold": quiz_data.get("pass_threshold", 70),
                    "xp": quiz_data.get("xp_reward", 50),
                }
                if quiz_id:
                    conn.execute(sa.text(f"""
                        UPDATE {schema}.quizzes SET
                            title = :title,
                            pass_threshold = :threshold,
                            xp_reward = :xp
                        WHERE id = :id
                    """), {**quiz_params, "id": quiz_id})
                else:
                    quiz_id = conn.execute(sa.text(f"""
                        INSERT INTO {schema}.quizzes
                            (lesson_id, title, pass_threshold, xp_reward)
                        VALUES (:lesson, :title, :threshold, :xp)
                        RETURNING id
                    """), quiz_params).scalar_one()

                for question_index, question in enumerate(quiz_data["questions"]):
                    question_id = conn.execute(sa.text(f"""
                        SELECT id FROM {schema}.quiz_questions
                        WHERE quiz_id = :quiz AND order_idx = :order_idx
                        ORDER BY id LIMIT 1
                    """), {
                        "quiz": quiz_id, "order_idx": question_index
                    }).scalar()
                    question_params = {
                        "quiz": quiz_id,
                        "text": question["question_text"],
                        "options": json.dumps(question["options"]),
                        "answer": question["correct_answer"],
                        "explanation": question.get("explanation", ""),
                        "order_idx": question_index,
                    }
                    if question_id:
                        conn.execute(sa.text(f"""
                            UPDATE {schema}.quiz_questions SET
                                question_text = :text,
                                options = CAST(:options AS jsonb),
                                correct_answer = :answer,
                                explanation = :explanation
                            WHERE id = :id
                        """), {**question_params, "id": question_id})
                    else:
                        conn.execute(sa.text(f"""
                            INSERT INTO {schema}.quiz_questions
                                (quiz_id, question_text, options, correct_answer,
                                 explanation, order_idx)
                            VALUES (:quiz, :text, CAST(:options AS jsonb), :answer,
                                    :explanation, :order_idx)
                        """), question_params)
        seeded.append(dict(course))
    return seeded
