# Anleitung für das Pixel Skript:

### Das Skript braucht folgende Angaben:

- `picture_folder`: Pfad zum Ordner, in dem die Bilder liegen
- `pixel_config`: Pfad zur Konfigurationsdatei im TOML Format, welche angiebt, welches Bild an welche Stelle muss
- `--config`: Kann mehrfach verwendet werden. Eine Konfiguration für einen Generierungsdurchlauf

Die Generatorkonfiguration hat folgenes Format:  
`--config min_prio;max_prio;png_path;prio_path;json_path;io;ip;ao;cmp`

Erklärung der Pfade:  
`png_path`: Das fertige Bild  
`prio_path`: Prioritätenmaske in schwarz weiß  
`json_path`: Json Datei, die vom Overlayskript oder Placerskript angenommen wird

Die einzlnen Parameter:

| Parameter |               Erlaubte Werte                | Default Wert |                                                                                                            Beschreibung                                                                                                             |
|:---------:|:-------------------------------------------:|:------------:|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|
| min_prio  |                0 <= x <= 255                |      10      |                                                                                     Alle Pixel mit einer geringeren Priorität werden ignoriert.                                                                                     |
| max_prio  |                0 <= x <= 255                |     250      |                                                                                      Alle Pixel mit einer höheren Priorität werden ignoriert.                                                                                       |
|  *_path   | Dateipfad oder<br/> Freitext oder<br/> `""` |      -       | Das entsprechende Ergebnis wird als base64 in stdout ausgegeben, wenn `base64:` am Anfang steht. Dann wird der Freitext mit Doppelpunkt vor die Ausgabe geschrieben<br/>Sonst wird die Ausgabe an dem entsprechenden Pfad abgelegt. |
|    io     |                `0` oder `1`                 |      -       |                                                                                Generiert die Ausgabe als Overlay (leerer Platz zwischen den Pixeln)                                                                                 |
|    ip     |                `0` oder `1`                 |      -       |                                                                                 Prioritäten komplett ignorieren; alle Pixel bekommen Priorität 255                                                                                  |
|    ao     |                `0` oder `1`                 |      -       |                                                                       Erlaube oder verbiete das Überschreiben von Pixeln durch Pixel einer höheren Priorität                                                                        |
|    cmp    |                `0` oder `1`                 |      -       |                                                            Alle Pixel, die eine höhere Priorität haben, als durch `max_prio' festgelegt, werden auf diesen Wert gesetzt                                                             |

`""` kennzeichnen einen "leeren Parameter" (wird dann ignoriert, Bsp: `10;250;;/tmp/prio.png;/tmp/json.png;1;1;1;1` oder `;;;/tmp/prio.png;/tmp/json.png;1;1;1;1` würde keine png Datei generieren, aber die Prio Datei )  
Beispiele:  
`20;200;/tmp/png.png;/tmp/prio.png;/tmp/json.json;0;0;0;0`  
`20;200;;/tmp/prio.png;/tmp/json.json;1;0;0;0`  
`20;200;/tmp/png.png;;/tmp/json.json;1;1;0;0`  
`20;200;/tmp/png.png;/tmp/prio.png;/tmp/json.json;0;0;0;0`  
