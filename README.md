# Musica

Musica és una aplicació d'escriptori senzilla per preparar recopilatoris d'àlbums en CD sense haver d'editar les propietats de cada pista una per una a l'Explorador de Windows.

## Funcionalitats

- Selecció d'una carpeta amb pistes d'àudio.
- Escaneig opcional de subcarpetes.
- Lectura de metadades existents i ús del nom del fitxer com a títol quan el fitxer no en té.
- Edició massiva de camps comuns:
  - àlbum,
  - intèrpret,
  - artista de l'àlbum,
  - any,
  - gènere.
- Edició individual de la pista seleccionada.
- Numeració automàtica segons l'ordre de la taula, amb format `1/12` o només `1`.
- Neteja massiva de fragments repetits als títols. Per exemple, si les pistes venen com `Maneras de Vivir_JPdownloader`, pots indicar `JPdownloader` i el títol quedarà com `Maneras de Vivir`.
- Escriptura de metadades amb [`mutagen`](https://mutagen.readthedocs.io/), compatible amb formats habituals com MP3, FLAC, M4A/ALAC, OGG/Opus, WAV, WMA i AIFF quan el contenidor admet etiquetes.

## Instal·lació per desenvolupar o provar amb Python

Cal Python 3.10 o superior.

```bash
python -m pip install -e .
```

## Ús amb Python

```bash
musica
```

També pots executar-la directament així:

```bash
python -m musica.app
```

## Crear un executable per Windows

Per no haver d'instal·lar Python a cada ordinador on vulguis fer servir Musica, genera un executable amb PyInstaller des d'un ordinador Windows que sí tingui Python instal·lat.

### Opció ràpida

Des de PowerShell o `cmd`, dins la carpeta del projecte:

```bat
scripts\build_windows.bat
```

Quan acabi, trobaràs l'aplicació aquí:

```text
dist\Musica\Musica.exe
```

Pots copiar tota la carpeta `dist\Musica` a un altre ordinador Windows i executar `Musica.exe` sense instal·lar Python.

### Opció manual

Si prefereixes fer-ho pas a pas:

```bash
python -m pip install -e ".[build]"
pyinstaller --noconfirm --clean --windowed --name Musica --collect-all mutagen src\musica\app.py
```

El mode recomanat és carpeta (`dist\Musica`) en comptes d'un sol `.exe`, perquè sol donar menys falsos positius d'antivirus i arrenca més ràpid.

> Important: crea l'executable a Windows si el vols per Windows. Un executable generat a Linux o macOS no servirà directament com a `.exe` de Windows.

## Flux recomanat

1. Prem **Selecciona carpeta…** i tria la carpeta on tens les pistes.
2. Revisa els títols i les metadades carregades.
3. Si totes les cançons tenen un fragment sobrant, escriu-lo a **Text a eliminar** i prem **Elimina aquest text de tots els títols**.
4. Escriu les dades comunes de l'àlbum i prem **Aplica als fitxers carregats**.
5. Prem **Numera segons l'ordre actual** si vols completar els números de pista.
6. Si cal, selecciona una pista i ajusta'n les dades a la pestanya **Pista seleccionada**.
7. Quan ho tinguis revisat, prem **Desa metadades**.

> Recomanació: abans de desar, fes una còpia de seguretat de la carpeta si les pistes són úniques o difícils de recuperar.

## Desenvolupament i proves

```bash
python -m pip install -e '.[test]'
pytest
```
