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

## Instal·lació

Cal Python 3.10 o superior.

```bash
python -m pip install -e .
```

## Ús

```bash
musica
```

També pots executar-la directament així:

```bash
python -m musica.app
```

Flux recomanat:

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
