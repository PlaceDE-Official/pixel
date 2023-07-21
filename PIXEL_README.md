# Anleitung für das Pixel-Skript:

### Das Skript braucht folgende Angaben:

- `picture_folder`: Pfad zum Ordner, in dem die Bilder liegen
- `pixel_config`: Pfad zur Konfigurationsdatei im TOML-Format, welche angibt, welches Bild an welche Stelle muss
- `--config`: Kann mehrfach verwendet werden. Eine Konfiguration für einen Generierungsdurchlauf

Die Generatorkonfiguration hat folgenes Format:  
`--config min_prio;max_prio;png_path;prio_path;png_prio_path;json_path;io;ip;ao;cmp`

Erklärung der Pfade:  
`png_path`: Das generierte Bild  
`prio_path`: Die generierte Prioritätenmaske in Graustufen (schwarz ist maximale Priorität). Wird nur beachtet,
wenn `ip` `0` ist.  
`png_prio_path`: Das generierte Bild mit Farbe und Prio in einem PNG (Prio ist Alpha-Kanal). Wird nur beachtet,
wenn `ip` `0` ist.  
`json_path`: Die generierte JSON-Datei, die vom Overlayskript oder Placerskript angenommen wird

Die einzelnen Parameter:

| Parameter |               Erlaubte Werte                | Default Wert |                                                                                                            Beschreibung                                                                                                             |
|:---------:|:-------------------------------------------:|:------------:|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|
| min_prio  |                0 <= x <= 255                |      10      |                                                                                     Alle Pixel mit einer geringeren Priorität werden ignoriert.                                                                                     |
| max_prio  |                0 <= x <= 255                |     250      |                                                                                      Alle Pixel mit einer höheren Priorität werden ignoriert.                                                                                       |
|  *_path   | Dateipfad oder<br/> Freitext oder<br/> `""` |      -       | Das entsprechende Ergebnis wird als base64 in stdout ausgegeben, wenn `base64:` am Anfang steht. Dann wird der Freitext mit Doppelpunkt vor die Ausgabe geschrieben<br/>Sonst wird die Ausgabe an dem entsprechenden Pfad abgelegt. |
|    io     |                `0` oder `1`                 |      -       |                                                                          Generiert die Ausgabe als Overlay (zwischen zwei Pixeln ist je ein leerer Pixel)                                                                           |
|    ip     |                `0` oder `1`                 |      -       |                                                                                 Prioritäten komplett ignorieren; alle Pixel bekommen Priorität 255                                                                                  |
|    ao     |                `0` oder `1`                 |      -       |                                                                       Erlaube oder verbiete das Überschreiben von Pixeln durch Pixel einer höheren Priorität                                                                        |
|    cmp    |                `0` oder `1`                 |      -       |                                                            Alle Pixel, die eine höhere Priorität haben, als durch `max_prio' festgelegt, werden auf diesen Wert gesetzt                                                             |

`""` kennzeichnen einen "leeren Parameter" (wird dann ignoriert, Bsp: `10;250;;/tmp/prio.png;/tmp/json.png;1;1;1;1`
oder `;;;/tmp/prio.png;;/tmp/json.png;1;1;1;1` würde keine PNG-Datei generieren, aber die Prio-Datei)  
Beispiele:  
`20;200;/tmp/png.png;/tmp/prio.png;;/tmp/json.json;0;0;0;0`  
`20;200;;/tmp/prio.png;;/tmp/json.json;1;0;0;0`  
`20;200;/tmp/png.png;;/tmp/picture_prio.png;/tmp/json.json;1;1;0;0`  
`20;200;/tmp/png.png;/tmp/prio.png;;/tmp/json.json;0;0;0;0`


------
toml Datei:

`ignored_colors`: alle Farben, die ignoriert werden sollen. Die Farben werden in Hex aber OHNE führendes # angegeben.  
`allowed_colors`: alle Farben, die ignoriert werden sollen. Die Farben werden in Hex aber OHNE führendes # angegeben.  
`width`: Breite des generierten Bildes  
`height`: Höhe des generierten Bildes  
`add-x`: Offset x (reddit nutzt negative Koordinaten); nach Addition muss kleinste Koordinate 0 sein!
`add-y`: Offset y (reddit nutzt negative Koordinaten); nach Addition muss kleinste Koordinate 0 sein!
`default_prio`: Default-Priorität für alle Bilder  
`structure` (Liste)

Jedes `structure` hat folgende Werte:

|       Parameter        |      Beispiel       | Optional |                               Beschreibung                               |
|:----------------------:|:-------------------:|:--------:|:------------------------------------------------------------------------:|
|          name          |     flagge-ost      |    N     |                  Name der Struktur, muss eindeutig sein                  |
|          file          |   flagge-ost.png    |    N     |                  Dateiname, relativ zu `picture_folder`                  |
|     priority_file      | flagge-ost-prio.png |    J     |         Dateiname für die Priodatei, relativ zu `picture_folder`         |
|         startx         |         100         |    N     | x (links-nach-rechts) Startwert, an den die Struktur gesetzt werden soll |
|         starty         |         100         |    N     |  y (oben-nach-unten) Startwert, an den die Struktur gesetzt werden soll  |
|        priority        |         127         |    J     |     Priorität für Pixel des Bildes, die keine eigene Priorität haben     |
|      overlay_only      |        false        |    J     |     Struktur nur im Overlay-Modus übernehmen, nicht in andere Bilder     |
| ignore_prio_in_picture |        false        |    J     |     Deaktiviert die "Alphachannelprio" aus dem Bild (siehe 3. unten)     |

255 ist die höchste Priorität.
Die Prioritäten der Pixel werden wie folgt berechnet (last match):

1. Default prio
2. Prio der Struktur, falls gegeben
3. Alpha-Channel des Pixels, falls das Bild einen solchen hat
4. Wert des roten Kanals des entsprechenden Pixels im Prio-PNG, falls es ein Prio-PNG gibt (die anderen Kanäle werden
   ignoriert)
