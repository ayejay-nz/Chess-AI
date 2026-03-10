#!/bin/bash

engine_location="\"$HOME/Cute_Chess-1.4.0-x86_64.AppImage\""
python_location="/usr/bin/python3"
uci_location=\"$(pwd)"/src/uci.py"\"

engine_strength=$1
tc=$2
games=$3
concurrency=$4

current_unix_time=$(date +%s)
output_file="./output/chessai_vs_sf"$engine_strength"_"$games"_"$tc"_"$current_unix_time".pgn"

command=$engine_location" cli -engine name=ChessAI cmd="$python_location" arg="$uci_location" proto=uci -engine name=SF"$engine_strength" cmd=stockfish proto=uci option.UCI_LimitStrength=true option.UCI_Elo="$engine_strength" option.Threads=1 -each tc="$tc" timemargin=50 -games "$games" -repeat -recover -concurrency "$concurrency" -pgnout "$output_file
echo $command
eval $command
