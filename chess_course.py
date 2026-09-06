"""Original, multilingual Chess Foundations I curriculum and guided exercises.

The interaction model and FEN/UCI data conventions were informed by the
Chessville sister project.  All learner-facing prose in this module is original
FastLearn material written for children aged 3–12.
"""

from __future__ import annotations

import json
from copy import deepcopy

import sqlalchemy as sa


LANGUAGES = ("en", "et", "lt", "es")
COURSE_SLUG = "chess-foundations"

EXERCISE_UI = {
    "en": {"check": "Check answer", "level": "Level", "place": "Choose a piece, then choose its square"},
    "et": {"check": "Kontrolli vastust", "level": "Tase", "place": "Vali malend ja seejärel selle ruut"},
    "lt": {"check": "Patikrinti atsakymą", "level": "Lygis", "place": "Pasirink figūrą, tada jos langelį"},
    "es": {"check": "Comprobar respuesta", "level": "Nivel", "place": "Elige una pieza y después su casilla"},
}


def _t(en, et, lt, es):
    return {"en": en, "et": et, "lt": lt, "es": es}


def _lesson(title, content, *, duration=8, xp=25):
    return {
        "title": title,
        "content_md": content,
        "content_type": "interactive",
        "duration_min": duration,
        "xp_reward": xp,
    }


CATALOG = [{
    "title": _t("Chess Foundations I", "Male alused I", "Šachmatų pagrindai I", "Fundamentos de ajedrez I"),
    "slug": COURSE_SLUG,
    "description": _t(
        "A playful first chess course for ages 3–12: meet the board and learn how rooks, bishops, queens, and knights move through guided puzzles.",
        "Mänguline esimene malekursus 3–12-aastastele: tutvu malelauaga ning õpi juhendatud ülesannetes vankri, oda, lipu ja ratsu käike.",
        "Žaismingas pirmasis šachmatų kursas 3–12 metų vaikams: susipažinkite su lenta ir spręsdami užduotis išmokite bokšto, rikio, valdovės ir žirgo ėjimų.",
        "Un primer curso de ajedrez para niños de 3 a 12 años: conoce el tablero y aprende a mover torres, alfiles, damas y caballos con ejercicios guiados.",
    ),
    "category": _t("Chess", "Male", "Šachmatai", "Ajedrez"),
    "difficulty": "beginner",
    "is_published": True,
    "modules": [
        {
            "title": _t("Meet the Chessboard", "Tutvu malelauaga", "Susipažinkite su lenta", "Conoce el tablero"),
            "lessons": [
                _lesson(
                    _t("Welcome to Chess", "Tere tulemast malemaailma", "Sveiki atvykę į šachmatus", "Bienvenido al ajedrez"),
                    _t(
                        """# Welcome to Chess

Chess is a thinking game for two players. One player uses the light pieces and the other uses the dark pieces. The players take turns: White moves first, then Black, then White again.

Every piece has its own way of moving. A good chess player looks carefully, makes a plan, and checks the board before moving. You do not need to hurry. In this course we will learn one piece at a time and practise on small, friendly boards.

**Remember:** look, think, move.""",
                        """# Tere tulemast malemaailma

Male on mõtlemismäng kahele mängijale. Üks mängija kasutab valgeid ja teine musti malendeid. Mängijad käivad kordamööda: valge alustab, siis käib must ja seejärel jälle valge.

Igal malendil on oma liikumisviis. Hea maletaja vaatab hoolikalt, teeb plaani ja kontrollib lauda enne käiku. Kiirustada pole vaja. Õpime ühe malendi kaupa ja harjutame väikestel sõbralikel laudadel.

**Pea meeles:** vaata, mõtle, käi.""",
                        """# Sveiki atvykę į šachmatus

Šachmatai yra mąstymo žaidimas dviem žaidėjams. Vienas žaidžia baltaisiais, kitas – juodaisiais. Žaidėjai eina paeiliui: pirmieji eina baltieji, tada juodieji ir vėl baltieji.

Kiekviena figūra juda savaip. Geras žaidėjas atidžiai žiūri, planuoja ir prieš eidamas dar kartą patikrina lentą. Skubėti nereikia. Mokysimės po vieną figūrą ir treniruosimės mažose, draugiškose padėtyse.

**Prisimink:** pažiūrėk, pagalvok, eik.""",
                        """# Bienvenido al ajedrez

El ajedrez es un juego de pensar para dos personas. Una juega con las piezas blancas y otra con las negras. Se juega por turnos: empiezan las blancas, siguen las negras y después vuelven las blancas.

Cada pieza se mueve de una manera distinta. Un buen jugador observa, hace un plan y revisa el tablero antes de mover. No hace falta correr. Aprenderemos una pieza cada vez y practicaremos en tableros pequeños y amistosos.

**Recuerda:** mira, piensa y mueve.""",
                    ),
                ),
                _lesson(
                    _t("Squares and Coordinates", "Ruudud ja koordinaadid", "Langeliai ir koordinatės", "Casillas y coordenadas"),
                    _t(
                        """# Squares and Coordinates

The chessboard has 64 squares: eight across and eight up. The letters **a–h** name the columns, called files. The numbers **1–8** name the rows, called ranks.

Every square gets a letter and a number. Find the file first, then the rank: the square on file d and rank 4 is **d4**. A light square is always in the bottom-right corner from each player's view.

Coordinates let us describe a move clearly, like giving an address to a piece.""",
                        """# Ruudud ja koordinaadid

Malelaual on 64 ruutu: kaheksa laiuti ja kaheksa kõrguti. Tähed **a–h** nimetavad püstjooni ehk liine. Numbrid **1–8** nimetavad rõhtjooni ehk ridu.

Igal ruudul on täht ja number. Leia kõigepealt liin ja siis rida: d-liini ja 4. rea ruut on **d4**. Mängija poolt vaadates on parempoolne alumine nurgaruut alati hele.

Koordinaadid annavad igale malendile täpse aadressi.""",
                        """# Langeliai ir koordinatės

Šachmatų lentoje yra 64 langeliai: po aštuonis į plotį ir aukštį. Raidės **a–h** žymi vertikalias linijas, o skaičiai **1–8** – horizontalias eiles.

Kiekvienas langelis turi raidę ir skaičių. Pirmiausia raskite liniją, tada eilę: d linijos ir 4 eilės langelis yra **d4**. Žiūrint iš žaidėjo pusės, apatinis dešinysis kampas visada šviesus.

Koordinatės yra tikslus figūros adresas.""",
                        """# Casillas y coordenadas

El tablero tiene 64 casillas: ocho de ancho y ocho de alto. Las letras **a–h** nombran las columnas y los números **1–8** nombran las filas.

Cada casilla tiene una letra y un número. Busca primero la columna y después la fila: la columna d y la fila 4 forman **d4**. Desde el lado de cada jugador, la esquina inferior derecha siempre es clara.

Las coordenadas son la dirección exacta de cada pieza.""",
                    ),
                ),
                _lesson(
                    _t("Meet the Pieces", "Tutvu malenditega", "Susipažinkite su figūromis", "Conoce las piezas"),
                    _t(
                        """# Meet the Pieces

Each player begins with 16 pieces: one king, one queen, two rooks, two bishops, two knights, and eight pawns. The rooks begin in the corners. Knights stand beside them, then bishops. The queen stands on her own colour, and the king takes the last middle square.

Pieces work best as a team. Some slide in straight or diagonal lines. Knights jump. Pawns and kings will arrive in Chess Foundations II.

For now, learn to recognise each shape and its starting home.""",
                        """# Tutvu malenditega

Mõlemal mängijal on alguses 16 malendit: kuningas, lipp, kaks vankrit, kaks oda, kaks ratsut ja kaheksa etturit. Vankrid alustavad nurkades. Nende kõrval seisavad ratsud ja siis odad. Lipp seisab oma värvi ruudul ning kuningas viimasel keskmisel ruudul.

Malendid on tugevad meeskonnana. Mõned liiguvad sirgelt või diagonaalis, ratsud hüppavad. Etturid ja kuningas tulevad kursusel Male alused II.

Praegu õpi kujusid ja nende algkodusid ära tundma.""",
                        """# Susipažinkite su figūromis

Kiekvienas žaidėjas pradeda su 16 figūrų: karaliumi, valdove, dviem bokštais, dviem rikiais, dviem žirgais ir aštuoniais pėstininkais. Bokštai stovi kampuose, šalia jų – žirgai, tada rikiai. Valdovė stovi savo spalvos langelyje, o karalius – likusiame viduriniame.

Figūros stipriausios veikdamos kartu. Vienos slysta tiesiomis ar įstrižomis linijomis, o žirgai šoka. Pėstininkus ir karalių sutiksime antrame kurse.

Dabar išmok atpažinti figūras ir jų pradines vietas.""",
                        """# Conoce las piezas

Cada jugador empieza con 16 piezas: un rey, una dama, dos torres, dos alfiles, dos caballos y ocho peones. Las torres van en las esquinas. A su lado están los caballos y después los alfiles. La dama ocupa una casilla de su propio color y el rey la casilla central restante.

Las piezas funcionan mejor en equipo. Algunas se deslizan en línea recta o diagonal; los caballos saltan. Los peones y el rey llegarán en Fundamentos de ajedrez II.

Por ahora, aprende a reconocer cada pieza y su casa inicial.""",
                    ),
                ),
            ],
        },
        {
            "title": _t("Rooks and Bishops", "Vankrid ja odad", "Bokštai ir rikiai", "Torres y alfiles"),
            "lessons": [
                _lesson(
                    _t("The Rook: Straight Lines", "Vanker: sirged jooned", "Bokštas: tiesios linijos", "La torre: líneas rectas"),
                    _t(
                        """# The Rook: Straight Lines

The rook slides any number of empty squares **up, down, left, or right**. It never moves diagonally and it cannot jump over another piece.

Imagine four bright beams shining from the rook. Follow each beam until the edge of the board or the first piece. If the first piece belongs to the other player, the rook may capture it by landing on its square.

Before moving, check all four directions.""",
                        """# Vanker: sirged jooned

Vanker liigub mööda vabu ruute nii kaugele kui soovib **üles, alla, vasakule või paremale**. Ta ei liigu diagonaalis ega hüppa üle teiste malendite.

Kujutle vankrist nelja valguskiirt. Järgi iga kiirt laua servani või esimese malendini. Kui esimene malend on vastase oma, võib vanker selle ruudule liikudes lüüa.

Enne käiku kontrolli kõiki nelja suunda.""",
                        """# Bokštas: tiesios linijos

Bokštas gali slinkti per bet kiek laisvų langelių **aukštyn, žemyn, kairėn arba dešinėn**. Jis nejuda įstrižai ir negali peršokti kitų figūrų.

Įsivaizduok keturis šviesos spindulius nuo bokšto. Sek kiekvieną iki lentos krašto arba pirmos figūros. Jei pirmoji figūra yra priešininko, bokštas gali ją nukirsti atsistodamas į jos langelį.

Prieš eidamas patikrink visas keturias kryptis.""",
                        """# La torre: líneas rectas

La torre se desliza tantas casillas libres como quiera **arriba, abajo, a la izquierda o a la derecha**. Nunca va en diagonal ni puede saltar sobre otra pieza.

Imagina cuatro rayos de luz que salen de la torre. Sigue cada uno hasta el borde o hasta la primera pieza. Si esa pieza es rival, la torre puede capturarla ocupando su casilla.

Antes de mover, revisa las cuatro direcciones.""",
                    ),
                ),
                _lesson(
                    _t("Rook Routes", "Vankri teekonnad", "Bokšto keliai", "Rutas de la torre"),
                    _t(
                        """# Rook Routes

A rook can often reach a faraway square in one move. If the target is not on the same file or rank, the rook usually needs two moves: one turn makes an L-shaped route.

Plan the whole route before the first move. Look for blockers, and stop whenever another piece closes the line. During a capture puzzle, the rook lands on the captured piece's square and continues from there.

The shortest safe route is usually the clearest plan.""",
                        """# Vankri teekonnad

Vanker jõuab sageli kaugele ühe käiguga. Kui sihtruut ei ole samal liinil ega real, vajab vanker tavaliselt kahte käiku: ühe pöördega tekib L-kujuline teekond.

Kavanda kogu tee enne esimest käiku. Otsi takistusi ja peatu, kui mõni malend joone sulgeb. Löömisülesandes maandub vanker löödud malendi ruudul ja jätkab sealt.

Kõige lühem turvaline tee on tavaliselt kõige selgem plaan.""",
                        """# Bokšto keliai

Bokštas dažnai pasiekia tolimą langelį vienu ėjimu. Jei tikslas nėra toje pačioje linijoje ar eilėje, dažniausiai reikia dviejų ėjimų – kelias vieną kartą pasisuka.

Suplanuok visą kelią dar prieš pirmą ėjimą. Ieškok kliūčių ir sustok, kai kita figūra uždaro liniją. Kirtimo užduotyje bokštas atsistoja į nukirstos figūros langelį ir tęsia iš ten.

Trumpiausias saugus kelias paprastai yra aiškiausias planas.""",
                        """# Rutas de la torre

Una torre puede llegar muy lejos en un solo movimiento. Si la meta no está en la misma fila o columna, normalmente necesita dos movimientos y un giro.

Planea la ruta completa antes de empezar. Busca obstáculos y detente cuando una pieza cierre la línea. En un ejercicio de capturas, la torre ocupa la casilla de la pieza capturada y continúa desde allí.

La ruta segura más corta suele ser el plan más claro.""",
                    ),
                ),
                _lesson(
                    _t("The Bishop: Diagonal Lines", "Oda: diagonaalid", "Rikis: įstrižainės", "El alfil: diagonales"),
                    _t(
                        """# The Bishop: Diagonal Lines

The bishop slides along diagonal lines. It may travel any number of empty squares, but it cannot turn during one move or jump over a piece.

A bishop that starts on a light square always stays on light squares. A bishop from a dark square always stays on dark squares. That is why each player begins with two bishops: together they can visit both colours.

Trace the four diagonal rays before choosing a move.""",
                        """# Oda: diagonaalid

Oda liigub mööda diagonaale. Ta võib läbida ükskõik kui palju vabu ruute, kuid ei saa ühe käigu ajal pöörata ega üle malendi hüpata.

Heledalt ruudult alustanud oda jääb alati heledatele ruutudele. Tumedalt alustanud oda jääb tumedatele. Seepärast on kummalgi mängijal kaks oda: koos jõuavad nad mõlemat värvi ruutudele.

Enne käiku jälgi kõiki nelja diagonaalset kiirt.""",
                        """# Rikis: įstrižainės

Rikis slysta įstrižomis linijomis. Jis gali keliauti per bet kiek laisvų langelių, bet per vieną ėjimą negali pasukti ar peršokti figūros.

Rikis, pradėjęs šviesiame langelyje, visada lieka šviesiuose. Pradėjęs tamsiame – tamsiuose. Todėl kiekvienas žaidėjas turi po du rikius: kartu jie pasiekia abiejų spalvų langelius.

Prieš pasirinkdamas ėjimą sek keturis įstrižus spindulius.""",
                        """# El alfil: diagonales

El alfil se desliza en diagonal por tantas casillas libres como quiera. No puede girar durante un movimiento ni saltar sobre otra pieza.

Un alfil que empieza en una casilla clara siempre permanece en casillas claras. Uno que empieza en una oscura siempre permanece en oscuras. Por eso cada jugador tiene dos alfiles: juntos alcanzan ambos colores.

Sigue los cuatro rayos diagonales antes de elegir.""",
                    ),
                ),
                _lesson(
                    _t("Bishop Routes", "Oda teekonnad", "Rikio keliai", "Rutas del alfil"),
                    _t(
                        """# Bishop Routes

A bishop can reach any open square of its own colour, sometimes in one move and sometimes after changing diagonal. It can never reach a square of the other colour.

To find a route, look for a middle square that lies on a diagonal from both the start and the goal. Check that no piece blocks either part. In capture puzzles, every landing square becomes the start of the next diagonal.

Keep the colour rule in mind; it is a quick way to test a plan.""",
                        """# Oda teekonnad

Oda jõuab igale vabale oma värvi ruudule, mõnikord ühe käiguga ja mõnikord diagonaali vahetades. Teist värvi ruudule ei jõua ta kunagi.

Tee leidmiseks otsi vaheruutu, mis on diagonaalil nii alguse kui sihiga. Kontrolli, et kummalgi teel pole takistust. Löömisülesandes saab igast maandumisruudust järgmise diagonaali algus.

Pea värvireeglit meeles – see kontrollib plaani kiiresti.""",
                        """# Rikio keliai

Rikis gali pasiekti bet kurį laisvą savo spalvos langelį: kartais vienu ėjimu, kartais pakeitęs įstrižainę. Kitos spalvos langelio jis nepasieks niekada.

Ieškodamas kelio rask tarpinį langelį, esantį įstrižai ir nuo pradžios, ir nuo tikslo. Patikrink, ar abi kelio dalys laisvos. Kirtimo užduotyje kiekvienas nusileidimo langelis tampa kitos įstrižainės pradžia.

Spalvos taisyklė padeda greitai patikrinti planą.""",
                        """# Rutas del alfil

Un alfil puede llegar a cualquier casilla libre de su color, a veces en un movimiento y otras cambiando de diagonal. Nunca puede alcanzar una casilla del otro color.

Busca una casilla intermedia que esté en diagonal tanto con el inicio como con la meta. Comprueba que nada bloquee los dos tramos. En ejercicios de captura, cada llegada inicia la diagonal siguiente.

La regla del color permite comprobar el plan rápidamente.""",
                    ),
                ),
            ],
        },
        {
            "title": _t("Queens and Knights", "Lipud ja ratsud", "Valdovės ir žirgai", "Damas y caballos"),
            "lessons": [
                _lesson(
                    _t("The Queen: Two Powers Together", "Lipp: kaks jõudu koos", "Valdovė: dvi galios kartu", "La dama: dos poderes juntos"),
                    _t(
                        """# The Queen: Two Powers Together

The queen combines the rook and bishop: she slides any number of empty squares along a rank, file, or diagonal. She cannot jump over pieces.

From the centre, the queen can see many squares, which makes her powerful. Power also means responsibility: moving the queen too early can let other pieces chase her. First ask whether the route is clear, then check where she will land.

Think in eight rays: four straight and four diagonal.""",
                        """# Lipp: kaks jõudu koos

Lipp ühendab vankri ja oda liikumise: ta liigub nii kaugele kui soovib mööda rida, liini või diagonaali. Üle malendite ta hüpata ei saa.

Laua keskel näeb lipp paljusid ruute ja on väga tugev. Jõuga kaasneb vastutus: liiga vara liikunud lippu võivad teised malendid taga ajada. Kontrolli kõigepealt, kas tee on vaba, ja siis maandumisruutu.

Mõtle kaheksale kiirele: neli sirget ja neli diagonaalset.""",
                        """# Valdovė: dvi galios kartu

Valdovė sujungia bokšto ir rikio judėjimą: ji slysta per bet kiek laisvų langelių eile, linija arba įstrižaine. Per figūras šokti negali.

Iš centro valdovė mato daug langelių, todėl yra labai galinga. Tačiau anksti išėjusią valdovę gali vaikytis kitos figūros. Pirmiausia patikrink, ar kelias laisvas, tada – kur ji nusileis.

Galvok apie aštuonis spindulius: keturis tiesius ir keturis įstrižus.""",
                        """# La dama: dos poderes juntos

La dama combina la torre y el alfil: se desliza tantas casillas libres como quiera por filas, columnas o diagonales. No puede saltar piezas.

Desde el centro ve muchas casillas y tiene gran poder. Pero una dama que sale demasiado pronto puede ser perseguida. Primero comprueba que la ruta esté libre y después revisa dónde aterrizará.

Piensa en ocho rayos: cuatro rectos y cuatro diagonales.""",
                    ),
                ),
                _lesson(
                    _t("Queen Routes", "Lipu teekonnad", "Valdovės keliai", "Rutas de la dama"),
                    _t(
                        """# Queen Routes

Because the queen moves straight and diagonally, she can reach any open square quickly. Start by asking whether the goal shares a rank, file, or diagonal with her. If it does, one clear move is enough. Otherwise, find a safe turning square.

Do not count only distance. A shorter route is useful only when no piece blocks it. In capture chains, plan the order so that every landing square opens the next line.

Strong plans connect one move to the next.""",
                        """# Lipu teekonnad

Kuna lipp liigub sirgelt ja diagonaalis, jõuab ta kiiresti igale vabale ruudule. Vaata esmalt, kas siht on temaga samal real, liinil või diagonaalil. Kui jah, piisab ühest vabast käigust. Muidu leia turvaline pöörderuut.

Ära loe ainult vahemaad. Lühike tee on kasulik vaid siis, kui miski seda ei blokeeri. Löömisahelas vali järjekord nii, et iga maandumine avaks järgmise joone.

Tugev plaan seob ühe käigu järgmisega.""",
                        """# Valdovės keliai

Kadangi valdovė juda tiesiai ir įstrižai, ji greitai pasiekia bet kurį laisvą langelį. Pirmiausia patikrink, ar tikslas yra toje pačioje eilėje, linijoje ar įstrižainėje. Jei taip, pakanka vieno laisvo ėjimo. Jei ne, rask saugų posūkio langelį.

Svarbus ne vien atstumas. Trumpas kelias geras tik tada, kai jo niekas neužstoja. Kirtimų grandinėje planuok tvarką, kad kiekvienas nusileidimas atvertų kitą liniją.

Geras planas sujungia vieną ėjimą su kitu.""",
                        """# Rutas de la dama

Como la dama se mueve recta y diagonalmente, llega pronto a cualquier casilla libre. Primero pregunta si la meta comparte fila, columna o diagonal. Si es así, basta un movimiento despejado. Si no, busca una casilla segura para girar.

No cuentes solo la distancia. Una ruta corta sirve únicamente si nada la bloquea. En una cadena de capturas, ordena los objetivos para que cada llegada abra la línea siguiente.

Los buenos planes conectan un movimiento con el siguiente.""",
                    ),
                ),
                _lesson(
                    _t("The Knight: An L-shaped Jump", "Ratsu: L-kujuline hüpe", "Žirgas: L formos šuolis", "El caballo: un salto en L"),
                    _t(
                        """# The Knight: An L-shaped Jump

The knight moves in an **L shape**: two squares in one straight direction and then one square sideways. It is the only piece that can jump over other pieces.

From the centre a knight may have eight choices. Near an edge it has fewer. A knight always changes square colour with every move: light to dark or dark to light.

Try saying the rhythm as you look: “two, then one.” Count from the knight's square, not from the square beside it.""",
                        """# Ratsu: L-kujuline hüpe

Ratsu liigub **L-kujuliselt**: kaks ruutu ühes sirges suunas ja siis ühe ruudu kõrvale. Ta on ainus malend, kes saab teistest üle hüpata.

Laua keskel võib ratsul olla kaheksa valikut, serva lähedal vähem. Ratsu vahetab iga käiguga ruudu värvi: heledalt tumedale või tumedalt heledale.

Ütle vaadates rütmi: „kaks ja siis üks“. Loenda ratsu ruudust, mitte kõrvalruudust.""",
                        """# Žirgas: L formos šuolis

Žirgas juda **L forma**: du langelius viena tiesia kryptimi ir tada vieną į šoną. Tai vienintelė figūra, galinti peršokti kitas figūras.

Lentos centre žirgas gali turėti aštuonis pasirinkimus, o prie krašto – mažiau. Kiekvienu ėjimu jis pakeičia langelio spalvą: iš šviesaus į tamsų arba atvirkščiai.

Žiūrėdamas kartok ritmą: „du, tada vienas“. Skaičiuok nuo žirgo langelio.""",
                        """# El caballo: un salto en L

El caballo se mueve en forma de **L**: dos casillas en una dirección recta y después una hacia un lado. Es la única pieza que puede saltar sobre otras.

Desde el centro puede tener ocho opciones; cerca del borde tiene menos. En cada salto cambia el color de su casilla: de clara a oscura o de oscura a clara.

Repite el ritmo mientras miras: «dos y después una». Cuenta desde la casilla del caballo.""",
                    ),
                ),
            ],
        },
    ],
}]


def _exercise(key, lesson, kind, fen, prompt, *, concepts, band, skw, public=None, answer=None):
    return {
        "source_key": key,
        "lesson_title": lesson,
        "exercise_type": kind,
        "fen": fen,
        "prompt": prompt,
        "concepts": concepts,
        "difficulty_band": band,
        "cognitive_layer": skw,
        "public": public or {},
        "answer": answer or {},
    }


EXERCISES = [
    _exercise("fl-chess-01a", "Welcome to Chess", "multiple_choice", "8/8/8/8/8/8/8/8 w - - 0 1",
        _t("Who moves first in chess?", "Kes teeb males esimese käigu?", "Kas šachmatuose eina pirmas?", "¿Quién mueve primero en ajedrez?"),
        concepts=["turns"], band=1, skw="knowledge",
        public={"choices": _t(["White", "Black", "The tallest player"], ["Valge", "Must", "Kõige pikem mängija"], ["Baltieji", "Juodieji", "Aukščiausias žaidėjas"], ["Las blancas", "Las negras", "El jugador más alto"])}, answer={"answer": 0}),
    _exercise("fl-chess-01b", "Welcome to Chess", "multiple_choice", "8/8/8/8/8/8/8/8 w - - 0 1",
        _t("What is the best habit before a move?", "Milline on parim harjumus enne käiku?", "Koks geriausias įprotis prieš ėjimą?", "¿Cuál es el mejor hábito antes de mover?"),
        concepts=["thinking"], band=1, skw="knowledge",
        public={"choices": _t(["Look and think", "Move as fast as possible", "Close your eyes"], ["Vaata ja mõtle", "Käi võimalikult kiiresti", "Sulge silmad"], ["Pažiūrėti ir pagalvoti", "Eiti kuo greičiau", "Užmerkti akis"], ["Mirar y pensar", "Mover lo más rápido posible", "Cerrar los ojos"])}, answer={"answer": 0}),
    _exercise("fl-chess-02a", "Squares and Coordinates", "multiple_choice", "8/8/8/8/3R4/8/8/8 w - - 0 1",
        _t("Which square holds the rook?", "Millisel ruudul seisab vanker?", "Kuriame langelyje stovi bokštas?", "¿En qué casilla está la torre?"),
        concepts=["coordinates"], band=1, skw="knowledge",
        public={"choices": _t(["c4", "d4", "d5", "e4"], ["c4", "d4", "d5", "e4"], ["c4", "d4", "d5", "e4"], ["c4", "d4", "d5", "e4"])}, answer={"answer": 1}),
    _exercise("fl-chess-02b", "Squares and Coordinates", "select_squares", "8/8/8/8/8/8/8/8 w - - 0 1",
        _t("Select every square on the d-file.", "Vali kõik d-liini ruudud.", "Pažymėk visus d linijos langelius.", "Selecciona todas las casillas de la columna d."),
        concepts=["coordinates"], band=2, skw="skill", answer={"targets": [f"d{rank}" for rank in range(1, 9)]}),
    _exercise("fl-chess-03a", "Meet the Pieces", "multiple_choice", "rnbqkbnr/8/8/8/8/8/8/RNBQKBNR w - - 0 1",
        _t("Which pieces begin in the four corners?", "Millised malendid alustavad neljas nurgas?", "Kurios figūros pradeda keturiuose kampuose?", "¿Qué piezas empiezan en las cuatro esquinas?"),
        concepts=["pieces"], band=1, skw="knowledge",
        public={"choices": _t(["Rooks", "Bishops", "Queens"], ["Vankrid", "Odad", "Lipud"], ["Bokštai", "Rikiai", "Valdovės"], ["Las torres", "Los alfiles", "Las damas"])}, answer={"answer": 0}),
    _exercise("fl-chess-03b", "Meet the Pieces", "place_pieces", "8/8/8/8/8/8/8/8 w - - 0 1",
        _t("Place the two white rooks in their starting corners.", "Aseta kaks valget vankrit algusnurkadesse.", "Pastatyk du baltuosius bokštus į jų pradinius kampus.", "Coloca las dos torres blancas en sus esquinas iniciales."),
        concepts=["pieces"], band=2, skw="skill", public={"pieces": ["R", "R"]}, answer={"placements": [{"square": "a1", "piece": "R"}, {"square": "h1", "piece": "R"}]}),
    _exercise("fl-chess-04a", "The Rook: Straight Lines", "select_squares", "8/8/8/8/3R4/8/8/8 w - - 0 1",
        _t("Select every square the rook can reach in one move.", "Vali kõik ruudud, kuhu vanker ühe käiguga jõuab.", "Pažymėk visus langelius, kuriuos bokštas pasiekia vienu ėjimu.", "Selecciona todas las casillas que la torre alcanza en un movimiento."),
        concepts=["rook-movement"], band=1, skw="skill", answer={"targets": ["a4", "b4", "c4", "e4", "f4", "g4", "h4", "d1", "d2", "d3", "d5", "d6", "d7", "d8"]}),
    _exercise("fl-chess-04b", "The Rook: Straight Lines", "multiple_choice", "8/8/8/8/3R4/8/8/8 w - - 0 1",
        _t("Can the rook move from d4 to g7?", "Kas vanker saab liikuda d4-lt g7-le?", "Ar bokštas gali eiti iš d4 į g7?", "¿Puede la torre ir de d4 a g7?"),
        concepts=["rook-movement"], band=2, skw="knowledge",
        public={"choices": _t(["Yes", "No, that is diagonal"], ["Jah", "Ei, see on diagonaal"], ["Taip", "Ne, tai įstrižainė"], ["Sí", "No, eso es diagonal"])}, answer={"answer": 1}),
    _exercise("fl-chess-05a", "Rook Routes", "path", "8/8/8/8/8/8/8/R7 w - - 0 1",
        _t("Guide the rook from a1 to h8 in exactly two moves.", "Juhi vanker a1-lt h8-le täpselt kahe käiguga.", "Nuvesk bokštą iš a1 į h8 lygiai dviem ėjimais.", "Lleva la torre de a1 a h8 en exactamente dos movimientos."),
        concepts=["rook-routes"], band=2, skw="skill", public={"goal": "h8", "optimal_len": 2}, answer={"goal": "h8", "optimal_len": 2}),
    _exercise("fl-chess-05b", "Rook Routes", "move_sequence", "r6n/8/8/8/3p3b/8/8/R7 w - - 0 1",
        _t("Capture both black pieces with the rook, one on each move.", "Löö vankriga mõlemad mustad malendid, üks kummalgi käigul.", "Bokštu nukirsk abi juodąsias figūras, po vieną kiekvienu ėjimu.", "Captura las dos piezas negras con la torre, una en cada movimiento."),
        concepts=["rook-routes"], band=3, skw="skill", answer={"capture_all": True}),
    _exercise("fl-chess-06a", "The Bishop: Diagonal Lines", "select_squares", "8/8/8/8/3B4/8/8/8 w - - 0 1",
        _t("Select every square the bishop can reach in one move.", "Vali kõik ruudud, kuhu oda ühe käiguga jõuab.", "Pažymėk visus langelius, kuriuos rikis pasiekia vienu ėjimu.", "Selecciona todas las casillas que el alfil alcanza en un movimiento."),
        concepts=["bishop-movement"], band=1, skw="skill", answer={"targets": ["a1", "b2", "c3", "e3", "f2", "g1", "a7", "b6", "c5", "e5", "f6", "g7", "h8"]}),
    _exercise("fl-chess-06b", "The Bishop: Diagonal Lines", "multiple_choice", "8/8/8/8/3B4/8/8/8 w - - 0 1",
        _t("A bishop starts on a light square. Which colours can it visit?", "Oda alustab heledal ruudul. Mis värvi ruutudele ta jõuab?", "Rikis pradeda šviesiame langelyje. Kokios spalvos langelius jis gali pasiekti?", "Un alfil empieza en una casilla clara. ¿Qué colores puede visitar?"),
        concepts=["bishop-movement"], band=2, skw="knowledge",
        public={"choices": _t(["Light only", "Dark only", "Both colours"], ["Ainult heledaid", "Ainult tumedaid", "Mõlemat värvi"], ["Tik šviesius", "Tik tamsius", "Abiejų spalvų"], ["Solo claras", "Solo oscuras", "Ambos colores"])}, answer={"answer": 0}),
    _exercise("fl-chess-07a", "Bishop Routes", "path", "8/8/8/8/8/8/8/B7 w - - 0 1",
        _t("Guide the bishop from a1 to g3 in exactly two moves.", "Juhi oda a1-lt g3-le täpselt kahe käiguga.", "Nuvesk rikį iš a1 į g3 lygiai dviem ėjimais.", "Lleva el alfil de a1 a g3 en exactamente dos movimientos."),
        concepts=["bishop-routes"], band=2, skw="skill", public={"goal": "g3", "optimal_len": 2}, answer={"goal": "g3", "optimal_len": 2}),
    _exercise("fl-chess-07b", "Bishop Routes", "move_sequence", "5n2/8/7b/8/8/p7/3r4/2B5 w - - 0 1",
        _t("Capture every black piece with the bishop, one piece per move.", "Löö odaga kõik mustad malendid, üks malend igal käigul.", "Rikiu nukirsk visas juodąsias figūras, po vieną per ėjimą.", "Captura todas las piezas negras con el alfil, una por movimiento."),
        concepts=["bishop-routes"], band=3, skw="skill", answer={"capture_all": True}),
    _exercise("fl-chess-08a", "The Queen: Two Powers Together", "select_squares", "8/8/8/8/3Q4/8/8/8 w - - 0 1",
        _t("Select every square the queen can reach in one move.", "Vali kõik ruudud, kuhu lipp ühe käiguga jõuab.", "Pažymėk visus langelius, kuriuos valdovė pasiekia vienu ėjimu.", "Selecciona todas las casillas que la dama alcanza en un movimiento."),
        concepts=["queen-movement"], band=2, skw="skill", answer={"targets": ["a4", "b4", "c4", "e4", "f4", "g4", "h4", "d1", "d2", "d3", "d5", "d6", "d7", "d8", "a1", "b2", "c3", "e3", "f2", "g1", "a7", "b6", "c5", "e5", "f6", "g7", "h8"]}),
    _exercise("fl-chess-08b", "The Queen: Two Powers Together", "multiple_choice", "8/8/8/8/3Q4/8/8/8 w - - 0 1",
        _t("Which two pieces have movement powers combined in the queen?", "Millise kahe malendi liikumine on lipus ühendatud?", "Kurių dviejų figūrų judėjimą sujungia valdovė?", "¿Qué dos piezas combinan sus movimientos en la dama?"),
        concepts=["queen-movement"], band=2, skw="knowledge",
        public={"choices": _t(["Rook and bishop", "Knight and rook", "Two knights"], ["Vanker ja oda", "Ratsu ja vanker", "Kaks ratsut"], ["Bokštas ir rikis", "Žirgas ir bokštas", "Du žirgai"], ["Torre y alfil", "Caballo y torre", "Dos caballos"])}, answer={"answer": 0}),
    _exercise("fl-chess-09a", "Queen Routes", "path", "8/8/8/8/8/8/8/Q7 w - - 0 1",
        _t("Guide the queen from a1 to d6 in exactly two moves.", "Juhi lipp a1-lt d6-le täpselt kahe käiguga.", "Nuvesk valdovę iš a1 į d6 lygiai dviem ėjimais.", "Lleva la dama de a1 a d6 en exactamente dos movimientos."),
        concepts=["queen-routes"], band=3, skw="skill", public={"goal": "d6", "optimal_len": 2}, answer={"goal": "d6", "optimal_len": 2}),
    _exercise("fl-chess-09b", "Queen Routes", "move_sequence", "3rn3/8/8/8/p6b/8/8/3Q4 w - - 0 1",
        _t("Capture every black piece with the queen, one piece per move.", "Löö lipuga kõik mustad malendid, üks malend igal käigul.", "Valdove nukirsk visas juodąsias figūras, po vieną per ėjimą.", "Captura todas las piezas negras con la dama, una por movimiento."),
        concepts=["queen-routes"], band=4, skw="wisdom", answer={"capture_all": True}),
    _exercise("fl-chess-10a", "The Knight: An L-shaped Jump", "select_squares", "8/8/8/8/3N4/8/8/8 w - - 0 1",
        _t("Select every square the knight can jump to.", "Vali kõik ruudud, kuhu ratsu saab hüpata.", "Pažymėk visus langelius, į kuriuos žirgas gali nušokti.", "Selecciona todas las casillas a las que puede saltar el caballo."),
        concepts=["knight-movement"], band=1, skw="skill", answer={"targets": ["b3", "b5", "c2", "c6", "e2", "e6", "f3", "f5"]}),
    _exercise("fl-chess-10b", "The Knight: An L-shaped Jump", "place_pieces", "r1b2b1r/8/8/8/8/8/8/R1B2B1R w - - 0 1",
        _t("Place the two white knights between the rooks and bishops.", "Aseta kaks valget ratsut vankrite ja odade vahele.", "Pastatyk du baltuosius žirgus tarp bokštų ir rikių.", "Coloca los dos caballos blancos entre las torres y los alfiles."),
        concepts=["knight-movement"], band=2, skw="skill", public={"pieces": ["N", "N"]}, answer={"placements": [{"square": "b1", "piece": "N"}, {"square": "g1", "piece": "N"}]}),
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
        **{lang: {field: deepcopy(record[field][lang]) for field in fields} for lang in LANGUAGES if lang != "en"},
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
    return result


CHESS_COURSES = _english(CATALOG)
CHESS_TRANSLATIONS = _build_translations()


def public_exercise(exercise: dict, lang: str = "en") -> dict:
    """Return a browser/API-safe exercise without its answer payload."""
    language = lang if lang in LANGUAGES else "en"
    public = {}
    for key, value in exercise.get("public", {}).items():
        public[key] = deepcopy(value.get(language, value.get("en"))) if isinstance(value, dict) and set(value) == set(LANGUAGES) else deepcopy(value)
    return {
        "source_key": exercise["source_key"],
        "engine": "chess",
        "exercise_type": exercise["exercise_type"],
        "fen": exercise["fen"],
        "prompt": exercise["prompt"][language],
        "concepts": exercise["concepts"],
        "difficulty_band": exercise["difficulty_band"],
        "cognitive_layer": exercise["cognitive_layer"],
        "ui": deepcopy(EXERCISE_UI[language]),
        **public,
    }


def seed_chess_course(conn, schema: str) -> dict:
    """Idempotently install the protected default course and its exercises."""
    course_data = CHESS_COURSES[0]
    owner_id = conn.execute(sa.text(f"SELECT id FROM {schema}.users WHERE lower(email) = 'kaljuvee@gmail.com' LIMIT 1")).scalar()
    course = conn.execute(sa.text(f"""
        INSERT INTO {schema}.courses
            (title, slug, description, category, difficulty, is_published, instructor_id, is_default)
        VALUES (:title, :slug, :description, :category, :difficulty, true, :owner, true)
        ON CONFLICT (slug) DO UPDATE SET
            title = EXCLUDED.title, description = EXCLUDED.description,
            category = EXCLUDED.category, difficulty = EXCLUDED.difficulty,
            is_published = true, is_default = true,
            instructor_id = COALESCE(EXCLUDED.instructor_id, {schema}.courses.instructor_id)
        RETURNING *
    """), {**{key: course_data[key] for key in ("title", "slug", "description", "category", "difficulty")}, "owner": owner_id}).mappings().one()

    lessons_by_title = {}
    for module_index, module_data in enumerate(course_data["modules"]):
        module_id = conn.execute(sa.text(f"""
            SELECT id FROM {schema}.modules WHERE course_id=:course AND title=:title ORDER BY id LIMIT 1
        """), {"course": course["id"], "title": module_data["title"]}).scalar()
        if not module_id:
            module_id = conn.execute(sa.text(f"""
                INSERT INTO {schema}.modules (course_id, title, order_idx)
                VALUES (:course, :title, :order_idx) RETURNING id
            """), {"course": course["id"], "title": module_data["title"], "order_idx": module_index}).scalar_one()
        else:
            conn.execute(sa.text(f"UPDATE {schema}.modules SET order_idx=:order_idx WHERE id=:id"), {"order_idx": module_index, "id": module_id})
        for lesson_index, lesson_data in enumerate(module_data["lessons"]):
            lesson_id = conn.execute(sa.text(f"""
                SELECT id FROM {schema}.lessons WHERE module_id=:module AND title=:title ORDER BY id LIMIT 1
            """), {"module": module_id, "title": lesson_data["title"]}).scalar()
            params = {
                "module": module_id, "title": lesson_data["title"], "content": lesson_data["content_md"],
                "content_type": "interactive", "duration": lesson_data["duration_min"],
                "xp": lesson_data["xp_reward"], "order_idx": lesson_index,
            }
            if lesson_id:
                conn.execute(sa.text(f"""
                    UPDATE {schema}.lessons SET content_md=:content, content_type=:content_type,
                        duration_min=:duration, xp_reward=:xp, order_idx=:order_idx WHERE id=:id
                """), {**params, "id": lesson_id})
            else:
                lesson_id = conn.execute(sa.text(f"""
                    INSERT INTO {schema}.lessons
                        (module_id, title, content_md, content_type, duration_min, xp_reward, order_idx)
                    VALUES (:module, :title, :content, :content_type, :duration, :xp, :order_idx)
                    RETURNING id
                """), params).scalar_one()
            lessons_by_title[lesson_data["title"]] = lesson_id

    for order_idx, exercise in enumerate(EXERCISES):
        public = public_exercise(exercise, "en")
        prompt = public.pop("prompt")
        public.pop("source_key", None)
        exercise_id = conn.execute(sa.text(f"""
            INSERT INTO {schema}.interactive_exercises
                (source_key, engine, exercise_type, fen, prompt, concepts,
                 difficulty_band, cognitive_layer, public_payload, answer_payload)
            VALUES (:source_key, 'chess', :exercise_type, :fen, :prompt, CAST(:concepts AS jsonb),
                    :band, :layer, CAST(:public AS jsonb), CAST(:answer AS jsonb))
            ON CONFLICT (source_key) DO UPDATE SET
                exercise_type=EXCLUDED.exercise_type, fen=EXCLUDED.fen, prompt=EXCLUDED.prompt,
                concepts=EXCLUDED.concepts, difficulty_band=EXCLUDED.difficulty_band,
                cognitive_layer=EXCLUDED.cognitive_layer, public_payload=EXCLUDED.public_payload,
                answer_payload=EXCLUDED.answer_payload
            RETURNING id
        """), {
            "source_key": exercise["source_key"], "exercise_type": exercise["exercise_type"],
            "fen": exercise["fen"], "prompt": prompt, "concepts": json.dumps(exercise["concepts"]),
            "band": exercise["difficulty_band"], "layer": exercise["cognitive_layer"],
            "public": json.dumps(public), "answer": json.dumps(exercise["answer"]),
        }).scalar_one()
        lesson_id = lessons_by_title[exercise["lesson_title"]]
        lesson_order = sum(1 for item in EXERCISES[:order_idx] if item["lesson_title"] == exercise["lesson_title"])
        conn.execute(sa.text(f"""
            INSERT INTO {schema}.lesson_exercises (lesson_id, exercise_id, order_idx)
            VALUES (:lesson, :exercise, :order_idx)
            ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET order_idx=EXCLUDED.order_idx
        """), {"lesson": lesson_id, "exercise": exercise_id, "order_idx": lesson_order})
        for language in LANGUAGES:
            localized = public_exercise(exercise, language)
            conn.execute(sa.text(f"""
                INSERT INTO {schema}.exercise_translations (exercise_id, language, prompt, public_payload)
                VALUES (:exercise, :language, :prompt, CAST(:public AS jsonb))
                ON CONFLICT (exercise_id, language) DO UPDATE SET
                    prompt=EXCLUDED.prompt, public_payload=EXCLUDED.public_payload
            """), {
                "exercise": exercise_id, "language": language, "prompt": localized.pop("prompt"),
                "public": json.dumps({key: value for key, value in localized.items() if key not in {
                "source_key", "engine", "exercise_type", "fen", "concepts", "difficulty_band", "cognitive_layer"
                }}),
            })
    return dict(course)
