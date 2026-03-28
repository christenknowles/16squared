# 16 Squared — Game Project

## What this project is
A 2-player strategy board game called "16 Squared" built with Python and Streamlit.
The player competes against an AI opponent on a 16x16 grid. Players place tokens in
straight lines starting from border squares, trying to build scoring lines that cross
the battlefield. The AI opponent is called "The Game."

## Deployment target
This game is hosted online via Streamlit Community Cloud for beta testers to play
in their browser. GitHub is the source — Streamlit Cloud auto-deploys on every push.
Performance, UI responsiveness, and clean session state management are priorities.

## Tech stack
- Python 3.14
- Streamlit (web app framework and UI)
- Matplotlib (board rendering)
- NumPy (board state as a 16x16 array)

## How to run locally
python -m streamlit run app.py

## How to install dependencies
python -m pip install streamlit matplotlib numpy

## Project files
- app.py — entire game in one file (engine, AI, UI, board drawing)
- CLAUDE.md — this file

## Key systems in app.py
- SixteenSquaredEngine — core game logic class
  - simulate_path() — validates and traces token placement paths
  - get_ai_move() — AI move selection (600 random samples, weighted scoring)
  - should_ai_pass() — decides if AI should skip its turn
  - calculate_scores() — counts valid scoring lines for each player
  - get_scoring_lines() — returns line coordinates for board highlighting
- draw_board() — Matplotlib board renderer with wood/felt visual theme
- Streamlit session_state — tracks board, turn, scores, new cells

## Coding conventions
- Keep all game logic inside SixteenSquaredEngine class
- Keep all drawing logic inside draw_board()
- Use st.session_state for all game state
- Board is a 16x16 NumPy array: 0=empty, 1=player, 2=AI
- Coordinates: board[y, x] — y is row, x is column
- Border squares: x==0, x==15, y==0, or y==15

## After every change
Always run the game with `python -m streamlit run app.py` and confirm no errors
appear in the terminal. Report any Python errors or Streamlit warnings found.

## Goals for improvement
- AI opponent strategy, difficulty, and decision making
- Game feel and responsiveness for online players
- Edge case handling in path validation
- Scoring accuracy and consistency
- UI improvements for players on different screen sizes
- Any other improvements that would make the game better