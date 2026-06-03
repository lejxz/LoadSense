# PDF: SmartCity_USJR_FlowerBoys ASEAN Roadmap

--- PAGE 1 ---
USJR
 
-
 
FlowerBoys
 
ASEAN
 
TECHNICAL
 
ROADMAP
 
 
TEMPLATE
 
Submission
 
Deadline:
 
May
 
17,
 
2026
 
Format:
 
PDF
 
(Strictly
 
maximum
 
5
 
pages)
 
Naming
 
Convention:
 
[Track]_[University]_[T eamName]_Roadmap.pdf
 
 
TEAM
 
INFORMATION
 
Team
 
Name
 
USJR
 
-
 
FlowerBoys
 
ASEAN
 
Institution
 
University
 
of
 
San
 
Jose-Recoletos
 
Country
 
Philippines
 
Track
 
[
 
✓
 
]
 
Smart
 
Cities
 
Team
 
Leader
 
Name
 
,
 
lejuene.delantar .24@usjr .edu.ph
,
 
LEJUENE DELANT AR
+639333210265
 
 
SECTION
 
1:
 
EXECUTIVE
 
SUMMARY
 
(PROBLEM-SOLUTION
 
FIT)
 
Public
 
transit
 
in
 
ASEAN
 
cities
 
—
 
particularly
 
Cebu,
 
Philippines
 
—
 
operates
 
with
 
minimal
 
real-time
 
visibility
 
on
 
either
 
side
 
of
 
the
 
vehicle
 
door.
 
Commuters
 
cannot
 
determine
 
a
 
vehicle's
 
occupancy
 
before
 
it
 
arrives,
 
nor
 
predict
 
arrival
 
times.
 
Drivers
 
routinely
 
exceed
 
legal
 
passenger
 
capacity
 
while
 
operators
 
lack
 
demand
 
data
 
for
 
efficient
 
fleet
 
allocation.
 
Traffic
 
congestion
 
costs
 
the
 
Philippine
 
economy
 
PHP
 
3.5
 
billion
 
daily
 
in
 
lost
 
productivity ,
 
a
 
crisis
 
worsened
 
by
 
absent
 
live
 
monitoring
 
that
 
enables
 
illegal
 
overloading
 
(
sabit
)
 
and
 
weakens
 
safety
 
compliance
 
enforcement
 
(JICA,
 
2018;
 
LTFRB,
 
2024).
 
In
 
Cebu,
 
commuters
 
already
 
report
 
peak-period
 
wait
 
times
 
exceeding
 
20
 
minutes,
 
and
 
existing
 
transit
 
technology
 
consistently
 
bypasses
 
low-income
 
passengers
 
who
 
depend
 
on
 
jeepneys
 
most.
 
LoadSense
 
is
 
a
 
dual-layer
 
intelligent
 
transportation
 
platform
 
designed
 
to
 
close
 
this
 
information
 
gap.
 
The
 
first
 
layer
 
is
 
an
 
in-vehicle
 
edge
 
AI
 
system:
 
an
 
overhead
 
camera
 
runs
 
YOLOv8-nano
 
offline,
 
performing
 
bidirectional
 
passenger
 
counting
 
and
 
classifying
 
occupancy
 
into
 
four
 
tiers
 
—
 
Green
 
(available),
 
Yellow
 
(filling),
 
Red
 
(at
 
capacity),
 
and
 
Blinking
 
Red
 
(overloaded)
 
—
 
displayed
 
via
 
a
 
windshield
 
LED
 
strip
 
visible
 
to
 
waiting
 
commuters.
 
The
 
second
 
layer
 
is
 
a
 
cloud
 
intelligence
 
system:
 
GPS
 
telemetry
 
feeds
 
a
 
server
 
that
 
predicts
 
arrival
 
times,
 
detects
 
route
 
deviations
 
and
 
driving
 
anomalies,
 
and
 
forecasts
 
demand.
 
Designed
 
to
 
retrofit
 
into
 
traditional
 
jeepneys
 
and
 
modern
 
PUVs
 
without
 
fleet
 
replacement,
 
LoadSense
 
targets
 
SDG
 
9
 
and
 
SDG
 
11.
 
 
1
 


--- PAGE 2 ---
USJR
 
-
 
FlowerBoys
 
ASEAN
 
SECTION
 
2:
 
TECHNICAL
 
ARCHITECTURE
 
2.1
 
System
 
Components:
 
Inputs
 
Processing
 
Core
 
Outputs
 
●
 
Overhead
 
camera
 
video
 
stream
 
(in-vehicle,
 
continuous)
 
●
 
GPS
 
coordinates
 
from
 
onboard
 
hardware
 
●
 
Historical
 
occupancy
 
logs
 
and
 
route
 
records
 
●
 
Commuter
 
natural-language
 
queries
 
(mobile
 
app)
 
●
 
Live
 
traffic
 
and
 
weather
 
API
 
feeds
 
 
Edge:
 
YOLOv8-nano
 
(Offline)
 
detects
 
passengers;
 
Telemetry
 
Packager
 
handles
 
online,
 
lightweight
 
cellular
 
transmission
 
of
 
state
 
data
 
to
 
the
 
cloud..
 
Cloud
 
Server:
 
Gradient
 
boosting
 
ETA
 
model;
 
LSTM
 
demand
 
forecasting;
 
route
 
deviation
 
and
 
driving
 
anomaly
 
detection.
 
 
NLP
 
Chatbot:
 
LLM
 
API
 
fusing
 
occupancy
 
+
 
ETA
 
for
 
boarding
 
recommendations
 
 
●
 
LED
 
strip
 
color
 
on
 
windshield
 
(Green
 
/
 
Yellow
 
/
 
Red
 
/
 
Blinking
 
Red
 
●
 
ETA
 
and
 
occupancy
 
on
 
commuter
 
mobile
 
app
 
●
 
Fleet
 
dispatching
 
alerts
 
on
 
operator
 
dashboard
 
●
 
Safety
 
anomaly
 
alerts
 
(operators
 
first,
 
users
 
after
 
verification)
 
2.2
 
Architecture
 
Diagram:
 
2
 


--- PAGE 3 ---
USJR
 
-
 
FlowerBoys
 
ASEAN
 
SECTION
 
3:
 
AI
 
APPROACH
 
&
 
MODEL
 
SELECTION
 
Field
 
Details
 
Primary
 
AI
 
Approach
 
[
 
✓
 
]
 
Machine
 
Learning
 
[
 
✓
 
]
 
NLP
 
[
 
✓
 
]
 
Computer
 
Vision
 
Model
 
Selection
 
●
 
YOLOv8-nano
 
(Ultralytics/PyT orch)
 
offline
 
edge
 
passenger
 
detection;
 
deployed
 
on
 
Raspberry
 
Pi
 
5
 
/
 
Jetson
 
Nano.
 
 
●
 
Facebook
 
Prophet
 
server-side
 
time-series
 
demand
 
forecasting
 
from
 
historical
 
occupancy
 
logs.
 
 
●
 
Gradient
 
Boosting
 
Regressor
 
(XGBoost)
 
ETA
 
prediction
 
from
 
GPS
 
+
 
traffic
 
+
 
weather
 
features.
 
 
●
 
LLM
 
API
 
Lightweight
 
cloud
 
LLM
 
—
 
NLP
 
boarding
 
recommendation
 
chatbot.
 
●
 
Stack:
 
Python,
 
C++,
 
PyTorch,
 
VS
 
Code,
 
FastAPI,
 
React
 
Native..
 
 
Reasoning
 
YOLOv8-nano
 
is
 
the
 
only
 
YOLO
 
variant
 
deployable
 
within
 
the
 
thermal
 
envelope
 
of
 
an
 
unattended
 
edge
 
device,
 
achieving
 
real-time
 
inference
 
without
 
cloud
 
dependency .
 
Gradient
 
boosting
 
generalizes
 
better
 
than
 
deep
 
ETA
 
models
 
during
 
cold-start
 
phases.
 
Facebook
 
Prophet
 
was
 
explicitly
 
selected
 
over
 
LSTM
 
for
 
demand
 
forecasting
 
because
 
it
 
handles
 
missing
 
data
 
and
 
irregular
 
reporting
 
intervals
 
gracefully—crucial
 
during
 
early
 
pilot
 
phases
 
with
 
sparse
 
telemetry .
 
The
 
LLM
 
chatbot
 
is
 
API-based
 
to
 
prevent
 
edge
 
compute
 
overhead.
 
 
 
SECTION
 
4:
 
DATA
 
STRATEGY
 
&
 
ETHICS
 
Field
 
Details
 
Data
 
Sources
 
●
 
Custom
 
collection:
 
Overhead
 
camera
 
footage
 
from
 
pilot
 
vehicles
 
for
 
YOLOv8
 
fine-tuning
 
(collected
 
under
 
written
 
operator
 
consent)
 
●
 
GPS
 
telemetry:
 
Real-time
 
position
 
data
 
from
 
installed
 
hardware
 
 
●
 
Open-source:
 
OpenStreetMap
 
(ODbL)
 
for
 
route
 
geometry;
 
MMDA/L TO
 
historical
 
traffic
 
records
 
for
 
ETA
 
model
 
training
 
 
●
 
Weather:
 
OpenW eatherMap
 
API
 
for
 
ETA
 
feature
 
inputs
 
 
●
 
System-generated:
 
Occupancy
 
logs
 
accumulated
 
by
 
LoadSense
 
edge
 
devices
 
during
 
pilot,
 
bootstrapping
 
the
 
demand
 
forecasting
 
model
 
 
Data
 
Quality
 
&
 
Cleaning
 
●
 
GPS
 
outliers
 
removed
 
via
 
speed
 
and
 
heading
 
sanity
 
filters
 
●
 
Camera
 
frames
 
with
 
severe
 
occlusion
 
or
 
insuf ficient
 
lighting
 
flagged
 
and
 
excluded
 
from
 
training
 
sets
 
●
 
Manual
 
spot-check
 
validation
 
of
 
occupancy
 
counts
 
during
 
pilot
 
phase
 
●
 
ETA
 
predictions
 
annotated
 
with
 
explicit
 
confidence
 
bounds
 
during
 
cold-start
 
period
 
 
Licensing
 
&
 
Legality
 
●
 
OpenStreetMap:
 
ODbL
 
permits
 
use
 
in
 
this
 
context.
 
●
 
OpenW eatherMap:
 
Standard
 
API
 
TOS
 
permits
 
use.
 
●
 
In-vehicle
 
camera
 
footage:
 
Collected
 
under
 
signed
 
data
 
collection
 
agreements
 
with
 
vehicle
 
operators.
 
Footage
 
is
 
processed
 
on-device;
 
raw
 
video
 
is
 
never
 
transmitted
 
or
 
stored
 
externally .
 
Retained
 
strictly
 
for
 
the
 
pilot
 
duration
 
and
 
deleted
 
upon
 
completion.
 
●
 
Custom
 
GPS
 
data:
 
governed
 
by
 
written
 
operator
 
policy;
 
no
 
third-party
 
sharing.
 
3
 

--- PAGE 4 ---
USJR
 
-
 
FlowerBoys
 
ASEAN
 
Bias
 
Mitigation
 
&
 
Fairness
 
●
 
Training
 
data
 
collected
 
across
 
multiple
 
routes,
 
time-of-day
 
windows,
 
and
 
vehicle
 
types
 
to
 
prevent
 
route-specific
 
or
 
temporal
 
bias
 
●
 
Occupancy
 
classification
 
is
 
strictly
 
threshold-based
 
with
 
no
 
passenger
 
profiling
 
by
 
appearance,
 
demographics,
 
or
 
identity
 
 
●
 
Commuter
 
recommendations
 
are
 
auditable
 
by
 
the
 
transport
 
authority
 
to
 
detect
 
systematic
 
disadvantage
 
to
 
specific
 
operators
 
or
 
routes
 
●
 
Driver
 
behavior
 
data
 
is
 
advisory
 
only;
 
due-process
 
review
 
required
 
before
 
any
 
disciplinary
 
use
 
—
 
no
 
automatic
 
sanctions
 
 
 
SECTION
 
5:
 
DEVELOPMENT
 
MILESTONES
 
(AGILE
 
ROADMAP)
 
Phase
 
Activity
 
/
 
Task
 
Tools
 
Used
 
Expected
 
Outcome
 
Sprint
 
1
 
 
(May
 
1-15)
 
●
 
Camera
 
test
 
footage
 
capture
 
on
 
pilot
 
vehicle
 
 
●
 
Datas