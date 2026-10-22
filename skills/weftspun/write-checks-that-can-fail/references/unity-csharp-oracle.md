# Running original Unity C# as an oracle under dotnet

Use when a C++ (or other) port of a Unity C# algorithm must be checked
against the original on recorded input, and the Unity editor is not an
option.

## Build

1. `dotnet new`-style console project (`net10.0`, `Nullable` and
   `ImplicitUsings` off, warnings for unused fields muted). Add the
   NuGet packages the sources import (`MathNet.Numerics`,
   `Newtonsoft.Json` for logging structs).
2. Copy the algorithm's source files UNCHANGED into `src/`. Pull in the
   small structs they reference from other folders (serialization
   structs, enums, one helper class) rather than stubbing them; drop
   pure-rendering files (mesh builders) entirely.
3. Write `shim/UnityShim.cs` in `namespace UnityEngine`, float-precision,
   grown by compile errors:
   - `Vector3`: `normalized` returns zero below magnitude 1e-5; `==` is
     `(a-b).sqrMagnitude < 9.99999944E-11f`; `Cross`, `Dot`, `Project`,
     `ProjectOnPlane`, `Angle`, `Reflect`, `Set`, indexer.
   - `Mathf` (with `Epsilon = 1.401298E-45f`, `Approximately`),
     `Quaternion` (AngleAxis, `*` Vector3), `Debug` (silent unless
     verbose), `Color`, `Time`, `Application` paths.
   - `MonoBehaviour` with `gameObject`/`transform` fields whose
     `InverseTransformPoint` is identity (inputs are already canvas-local).
4. Replace a `MonoBehaviour` base class (e.g. `Stroke`) with a stub that
   keeps only the members the algorithm calls. In the class that finds
   its context in `Awake` via `GetComponentInParent`, swap `Awake` for an
   explicit `Init(context)`. That is the only edit to original files;
   record it in the file.
5. Read private state (e.g. a graph's private cycle set) by reflection
   from the driver, so the originals stay untouched.

## Drive

- Port the replay driver from the port's own session replayer
  line for line (constraint-to-anchor mapping, which old stroke a
  constraint resolves to, mirror handling, patch-id sink), but call the
  original classes. Then any difference isolates to the ported classes.
- Emit the same per-event format as the port's event tool
  (`state<TAB>a,b;c,d` of cycles added) so one comparison script reads
  both and the original app's log.
- Compare against the port built in its original-behaviour mode when
  the port has opt-in fixes, otherwise every fixed case shows as a
  difference.
- Planted control: an env switch that skips one call in the oracle only
  (e.g. the mirrored tap); the comparison must report differing events.
