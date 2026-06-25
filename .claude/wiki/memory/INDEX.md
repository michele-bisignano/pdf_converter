# Project Memory Index

Index give context. Read index first. 
Open target file save tokens. Stop read all.

| File | When read |
|---|---|
| architecture.md | Learn structure. Learn modules. Learn dependencies. Learn data flow. |
| decisions.md | Read before change architecture. Check past choices. Check why. |
| gotchas.md | Hit weird bug. Check known issue. |

> Rule: Add memory file update index. Drop update lose file.

## Add Memory File
Topic grow make file (`auth.md`, `deploy.md`, `db-schema.md`). Save `./.calude/wiki/memory/`. Add table row. Add short description.

## Raw Folder
Folder `./.calude/wiki/raw/` hold raw data. Hold specs. Hold notes. Hold external docs.
System skip folder search. User prompt "distill raw" read folder. Extract project data. Write `.calude/wiki/memory/` files. Make new file update index.