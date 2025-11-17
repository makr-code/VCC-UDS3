# UDS3 Workflow and Process Management

**Status:** Research Feature / Production Ready ✅  
**Modules:** `api/workflow.py`, `api/petrinet.py`  
**Lines of Code:** 1,044 (559 + 485)  
**References:** 104 files across codebase

---

## Overview

UDS3 includes comprehensive workflow and process management capabilities based on Petri net theory and formal verification methods. The system supports BPMN/EPK modeling, soundness verification, performance analysis, and administrative process modeling.

### Key Features

- **Petri Net Support:** Classical and colored Petri nets
- **Soundness Verification:** Van der Aalst soundness checking
- **BPMN/EPK Conversion:** Convert business process models to Petri nets
- **Workflow Analysis:** Structural and behavioral analysis
- **VPB Integration:** Verwaltungsprozess-Backbone (administrative process backbone)
- **Process Mining:** Analyze process execution from event logs
- **Token-Flow Simulation:** Simulate process execution
- **Deadlock Detection:** Identify potential deadlocks

---

## Architecture

### Workflow Stack

```
┌─────────────────────────────────────────────┐
│         Process Modeling Layer              │
│    (BPMN, EPK, Administrative Workflows)    │
├─────────────────────────────────────────────┤
│      Conversion Layer                        │
│  ┌──────────────┐  ┌──────────────┐         │
│  │ BPMN Parser  │  │  EPK Parser  │         │
│  └──────────────┘  └──────────────┘         │
├─────────────────────────────────────────────┤
│      Petri Net Core                          │
│  ┌──────────────┐  ┌──────────────┐         │
│  │  Workflow    │  │   Soundness  │         │
│  │  Analyzer    │  │   Verifier   │         │
│  └──────────────┘  └──────────────┘         │
├─────────────────────────────────────────────┤
│      Storage Layer                           │
│  (Neo4j for process graphs)                  │
└─────────────────────────────────────────────┘
```

### Petri Net Components

```
Places (◯)  = States/Conditions
Transitions (▯) = Events/Activities
Arcs (→)    = Flow relationships
Tokens (•)  = Process instances

Example Workflow:
   Start          Process         Approve        End
    ◯ → ▯Process → ◯ → ▯Approve → ◯ → ▯Complete → ◯
    •                                              
```

---

## Core Components

### PetriNet

Base Petri net class:

```python
@dataclass
class PetriNet:
    name: str
    places: List[Place]           # States/conditions
    transitions: List[Transition] # Activities/events
    arcs: List[Arc]               # Flow connections
    initial_marking: Dict[str, int]  # Initial tokens
    net_type: PetriNetType        # WORKFLOW_NET, STATE_MACHINE, etc.
```

### Place

Represents a state or condition:

```python
@dataclass
class Place:
    id: str
    name: str
    tokens: int = 0               # Current marking
    capacity: Optional[int] = None  # Max tokens (bounded)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Transition

Represents an activity or event:

```python
@dataclass
class Transition:
    id: str
    name: str
    enabled: bool = False         # Can fire?
    guard_condition: Optional[str] = None  # Firing condition
    cost: float = 1.0             # Execution cost/time
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### WorkflowNet

Special Petri net type for business processes:

```python
@dataclass
class WorkflowNet(PetriNet):
    """
    Workflow-Net nach van der Aalst:
    - Genau ein Start-Place (source)
    - Genau ein End-Place (sink)
    - Alle Knoten auf Pfad von Start zu End
    """
    start_place: str              # Single source
    end_place: str                # Single sink
    soundness: SoundnessLevel     # Verification result
```

---

## Usage Examples

### Creating a Workflow

```python
from api.workflow import WorkflowNetAnalyzer
from api.petrinet import PetriNet, Place, Transition, Arc

# Define workflow
net = PetriNet(name="Building Permit Process")

# Add places (states)
start = Place(id="start", name="Application Received", tokens=1)
review = Place(id="review", name="Under Review")
approved = Place(id="approved", name="Approved")
rejected = Place(id="rejected", name="Rejected")
end = Place(id="end", name="Process Complete")

net.add_places([start, review, approved, rejected, end])

# Add transitions (activities)
check = Transition(id="check", name="Check Application")
approve = Transition(id="approve", name="Approve")
reject = Transition(id="reject", name="Reject")
complete = Transition(id="complete", name="Complete Process")

net.add_transitions([check, approve, reject, complete])

# Add arcs (flow)
net.add_arc(start, check)
net.add_arc(check, review)
net.add_arc(review, approve)
net.add_arc(review, reject)
net.add_arc(approve, approved)
net.add_arc(reject, rejected)
net.add_arc(approved, complete)
net.add_arc(rejected, complete)
net.add_arc(complete, end)
```

### Soundness Verification

```python
from api.workflow import WorkflowNetAnalyzer

analyzer = WorkflowNetAnalyzer()

# Convert to workflow net
workflow = analyzer.to_workflow_net(
    net,
    start_place="start",
    end_place="end"
)

# Verify soundness
result = analyzer.verify_soundness(workflow)

print(f"Soundness Level: {result.soundness_level.value}")
print(f"Is Sound: {result.is_sound}")
print(f"Issues: {result.issues}")

# Soundness conditions checked:
# 1. Option to complete (can always reach end)
# 2. Proper completion (exactly 1 token in end)
# 3. No dead transitions (all reachable)
```

### BPMN Conversion

```python
from vpb.parser_bpmn import BPMNParser

# Parse BPMN file
parser = BPMNParser()
bpmn_model = parser.parse_file("building_permit_process.bpmn")

# Convert to Petri net
petri_net = parser.to_petri_net(bpmn_model)

# Analyze converted workflow
analyzer = WorkflowNetAnalyzer()
soundness_result = analyzer.verify_soundness(petri_net)
```

### EPK Conversion

```python
from vpb.parser_epk import EPKParser

# Parse EPK (Ereignisgesteuerte Prozesskette)
parser = EPKParser()
epk_model = parser.parse_file("verwaltungsprozess.epk")

# Convert to Petri net
petri_net = parser.to_petri_net(epk_model)

# Verify correctness
validation = petri_net.validate()
if not validation.is_valid:
    print(f"Errors: {validation.errors}")
```

### Process Simulation

```python
# Simulate token flow
simulator = analyzer.create_simulator(workflow)

# Run simulation
for step in range(10):
    # Get enabled transitions
    enabled = simulator.get_enabled_transitions()
    
    # Fire transition
    if enabled:
        transition = enabled[0]
        simulator.fire_transition(transition)
        print(f"Step {step}: Fired {transition.name}")
        
    # Check current state
    marking = simulator.get_current_marking()
    print(f"Tokens: {marking}")
```

---

## Soundness Verification

### Van der Aalst Soundness Criteria

1. **Option to Complete:**
   - From every reachable state, the end state can be reached
   - No dead ends or infinite loops

2. **Proper Completion:**
   - When end is reached, exactly 1 token in end place
   - No tokens left in intermediate places

3. **No Dead Transitions:**
   - Every transition can fire on at least one path from start to end
   - No unreachable activities

### Soundness Levels

```python
class SoundnessLevel(Enum):
    NOT_SOUND = "not_sound"           # Fails basic criteria
    RELAXED_SOUND = "relaxed_sound"   # Weak soundness
    SOUND = "sound"                   # Classical soundness ✅
    STRICT_SOUND = "strict_sound"     # Strongest guarantees
```

### Verification Example

```python
result = analyzer.verify_soundness(workflow)

if result.soundness_level == SoundnessLevel.SOUND:
    print("✅ Workflow is sound - safe to deploy")
elif result.soundness_level == SoundnessLevel.NOT_SOUND:
    print("❌ Workflow has issues:")
    for issue in result.issues:
        print(f"  - {issue.description}")
        print(f"    Location: {issue.location}")
        print(f"    Severity: {issue.severity}")
```

---

## Structural Analysis

### Free-Choice Detection

```python
# Check if workflow is free-choice
is_free_choice = analyzer.is_free_choice(workflow)

# Free-choice property:
# - Each place has at most one outgoing arc, OR
# - All outgoing arcs lead to transitions with no other input
```

### State Machine Detection

```python
# Check if workflow is a state machine
is_state_machine = analyzer.is_state_machine(workflow)

# State machine property:
# - Each transition has exactly one input and one output place
# - Sequential behavior only
```

### Marked Graph Detection

```python
# Check if workflow is a marked graph
is_marked_graph = analyzer.is_marked_graph(workflow)

# Marked graph property:
# - Each place has exactly one input and one output transition
# - Parallel behavior without synchronization
```

---

## Performance Analysis

### Cycle Time Analysis

```python
# Analyze expected cycle time
analysis = analyzer.analyze_cycle_time(workflow)

print(f"Average Cycle Time: {analysis.average_time}")
print(f"Best Case: {analysis.best_case_time}")
print(f"Worst Case: {analysis.worst_case_time}")
print(f"Bottlenecks: {analysis.bottlenecks}")
```

### Resource Analysis

```python
# Analyze resource requirements
resource_analysis = analyzer.analyze_resources(workflow)

print(f"Max Concurrent Tasks: {resource_analysis.max_concurrency}")
print(f"Resource Utilization: {resource_analysis.utilization}%")
print(f"Idle Time: {resource_analysis.idle_time}%")
```

### Bottleneck Detection

```python
# Identify bottlenecks
bottlenecks = analyzer.find_bottlenecks(workflow)

for bottleneck in bottlenecks:
    print(f"Bottleneck: {bottleneck.transition.name}")
    print(f"  Wait time: {bottleneck.avg_wait_time}")
    print(f"  Utilization: {bottleneck.utilization}%")
    print(f"  Recommendation: {bottleneck.recommendation}")
```

---

## VPB Integration

### Administrative Process Backbone

The VPB (Verwaltungsprozess-Backbone) provides standardized administrative workflows:

```python
from vpb.adapter import VPBAdapter

vpb = VPBAdapter()

# Load standard administrative process
process = vpb.load_process("building_permit_procedure")

# Get process as Petri net
workflow = vpb.to_workflow_net(process)

# Verify compliance with VPB standards
compliance = vpb.check_compliance(workflow)
if compliance.is_compliant:
    print("✅ Process complies with VPB standards")
```

### Process Templates

```python
# Use predefined templates
templates = vpb.list_templates()
# Returns: [
#   "building_permit",
#   "objection_procedure",
#   "freedom_of_information_request",
#   ...
# ]

# Instantiate template
template = vpb.get_template("building_permit")
workflow = template.to_workflow_net()
```

---

## Process Mining

### Event Log Analysis

```python
from api.workflow import ProcessMiner

miner = ProcessMiner()

# Load event log
event_log = [
    {"case_id": 1, "activity": "receive_application", "timestamp": "2024-01-01 10:00"},
    {"case_id": 1, "activity": "check_completeness", "timestamp": "2024-01-01 10:15"},
    {"case_id": 1, "activity": "approve", "timestamp": "2024-01-01 11:00"},
    ...
]

# Discover process model
discovered_net = miner.discover_process(event_log)

# Check conformance
conformance = miner.check_conformance(
    event_log,
    reference_workflow=workflow
)

print(f"Conformance Rate: {conformance.fitness:.2%}")
print(f"Deviations: {len(conformance.deviations)}")
```

---

## Advanced Features

### Colored Petri Nets

```python
# Support for data types on tokens
colored_net = ColoredPetriNet(name="Document Processing")

# Places with typed tokens
application_place = Place(
    id="applications",
    token_type="Application",  # Custom type
    tokens=[
        {"id": 1, "type": "building_permit", "status": "new"},
        {"id": 2, "type": "objection", "status": "pending"}
    ]
)

# Transitions with guards
approve_transition = Transition(
    id="approve",
    guard="token.status == 'complete' and token.valid == True"
)
```

### Hierarchical Workflows

```python
# Subprocess support
main_workflow = WorkflowNet(name="Main Process")
sub_workflow = WorkflowNet(name="Document Check")

# Embed subprocess
main_workflow.add_subprocess(
    subprocess=sub_workflow,
    interface_places={"in": "docs_to_check", "out": "docs_checked"}
)
```

---

## Integration Examples

### With Neo4j

```python
# Store workflow in Neo4j graph
from database.database_api_neo4j import Neo4jAPI

neo4j = Neo4jAPI()

# Save workflow as graph
neo4j.store_workflow(
    workflow,
    namespace="administrative_processes"
)

# Query similar workflows
similar = neo4j.find_similar_workflows(
    workflow,
    similarity_threshold=0.8
)
```

### With VPB Operations

```python
from vpb.operations import VPBOperations

ops = VPBOperations()

# Execute workflow step
result = ops.execute_step(
    workflow_id="building_permit_001",
    step="check_completeness",
    input_data={"application_id": 12345}
)

# Track execution
status = ops.get_execution_status(workflow_id)
print(f"Current Step: {status.current_step}")
print(f"Completion: {status.completion_percentage}%")
```

---

## API Reference

### WorkflowNetAnalyzer Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `verify_soundness()` | Check soundness | SoundnessResult |
| `is_free_choice()` | Free-choice check | bool |
| `is_state_machine()` | State machine check | bool |
| `find_bottlenecks()` | Find bottlenecks | List[Bottleneck] |
| `analyze_cycle_time()` | Cycle time analysis | CycleTimeAnalysis |
| `simulate()` | Simulate execution | SimulationResult |

### PetriNet Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `add_place()` | Add place | None |
| `add_transition()` | Add transition | None |
| `add_arc()` | Add flow arc | None |
| `fire_transition()` | Fire transition | bool |
| `get_enabled()` | Get enabled transitions | List[Transition] |
| `validate()` | Validate structure | ValidationResult |

---

## Best Practices

### 1. Always Verify Soundness

```python
# Before deploying workflow
result = analyzer.verify_soundness(workflow)
if not result.is_sound:
    raise ValueError("Workflow not sound - cannot deploy")
```

### 2. Use Templates

```python
# Prefer VPB templates over custom workflows
workflow = vpb.get_template("building_permit")
# Customize as needed
workflow.add_custom_step(...)
```

### 3. Test with Simulation

```python
# Simulate before production
simulator = analyzer.create_simulator(workflow)
for _ in range(100):  # 100 test cases
    simulator.run_random_execution()
```

### 4. Monitor Performance

```python
# Regular performance analysis
monthly_analysis = analyzer.analyze_execution_logs(
    workflow_id,
    period="last_30_days"
)
```

---

## Troubleshooting

### Workflow Not Sound

**Problem:** Soundness verification fails

**Solutions:**
1. Check for deadlocks (circular dependencies)
2. Verify all transitions are reachable
3. Ensure single start and end place
4. Check for proper completion (no orphan tokens)

### Simulation Deadlock

**Problem:** Simulation gets stuck

**Solutions:**
1. Check for missing arcs
2. Verify guard conditions
3. Check token availability
4. Use deadlock detection: `analyzer.detect_deadlocks(workflow)`

### Poor Performance

**Problem:** Workflow executes slowly

**Solutions:**
1. Run bottleneck analysis
2. Parallelize independent activities
3. Reduce synchronization points
4. Optimize resource allocation

---

## Related Documentation

- [VPB Architecture](../UDS3_VERWALTUNGSARCHITEKTUR.md) - Administrative architecture
- [Petrinet Workflow Analyzer](../UDS3_PETRINET_WORKFLOW_ANALYZER.md) - Detailed analyzer docs
- [VPB Naming Conventions](../UDS3_VBP_NAMENSKONVENTIONEN.md) - Naming standards

---

**Last Updated:** November 17, 2025  
**Version:** 1.5.0  
**Status:** Production Ready ✅ (Core), Research Feature (Advanced)  
**Compliance:** VPB Standards compatible
