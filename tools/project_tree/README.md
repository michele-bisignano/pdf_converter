# Project Tree Generator

Genera e mantiene aggiornato il file `docs/project_structure/repository_tree.md` con la struttura ad albero del repository.

## Utilizzo

```bash
python tools/project_tree/generate_tree.py
```

## Pre-commit Hook (opzionale)

Installa un hook git che rigenera automaticamente il tree ad ogni commit:

```bash
python tools/project_tree/setup_hook.py
```

## License

Copyright 2026 Michele Bisignano & Mattia Franchini

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
