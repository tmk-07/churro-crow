import initSource from "../../onsets_engine/__init__.py?raw";
import browserApiSource from "../../onsets_engine/browser_api.py?raw";
import checkerSource from "../../onsets_engine/checker.py?raw";
import expressionsSource from "../../onsets_engine/expressions.py?raw";
import modelsSource from "../../onsets_engine/models.py?raw";
import notationSource from "../../onsets_engine/notation.py?raw";
import restrictionsSource from "../../onsets_engine/restrictions.py?raw";
import solverSource from "../../onsets_engine/solver.py?raw";
import variationsSource from "../../onsets_engine/variations.py?raw";

export const ENGINE_SOURCES: Record<string, string> = {
  "__init__.py": initSource,
  "browser_api.py": browserApiSource,
  "checker.py": checkerSource,
  "expressions.py": expressionsSource,
  "models.py": modelsSource,
  "notation.py": notationSource,
  "restrictions.py": restrictionsSource,
  "solver.py": solverSource,
  "variations.py": variationsSource,
};
