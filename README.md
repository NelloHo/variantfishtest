# variantfishtest

This is a clone of [vairiantfishtest](https://github.com/ianfab/variantfishtest) with a GUI support.

variantfishtest.py is a python script to run matches between two given UCI chess variant engines. It is mainly used for testing of [Fairy-Stockfish](https://github.com/ianfab/Fairy-Stockfish) for variants not supported by [cutechess](https://github.com/cutechess/cutechess).

The script is variant-agnostic and therefore supports arbitrary variants, and relies on the correctness and consistency of the engines' rule implementation. A similar script with rule-aware game adjudication is [fairyfishtest](https://github.com/ianfab/fairyfishtest), which uses the CECP/xboard protocol to run matches.

Run `python variantfishtest.py -h` for instructions on usage.

### USAGE

You need to have python and pip on your PC.

Open cmd, `cd` to this variantfishtest directory , then type
```
pip install -r requirements.txt
```
Once you finished , type 
```
python gui.py
```
the GUI will open automatically

### Output
A typical output looks like
```
ELO: 103.73 +-71.1 (95%) LOS: 99.9%
Total: 100 W: 63 L: 34 D: 3
```
This means that 
* Engine 1 is 103.73 Elo stronger than engine 2 with a statistical uncertainty of 71.1 Elo at a 95% [confidence level](https://en.wikipedia.org/wiki/Confidence_interval).
* Its [likelihood of superiority (LOS)](https://www.chessprogramming.org/Match_Statistics#Likelihood_of_superiority) is 99.9%.
* It played 100 games, with 63 wins, 34 losses, and 3 draws.
