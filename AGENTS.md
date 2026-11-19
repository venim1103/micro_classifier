# Project Agent Workflow

These instructions apply to any AI assistant working in this repository.
Apply them within higher-priority platform, tool and safety requirements; do
not promise capabilities or indefinite turn lifetime that the environment lacks.

**Active continuation rule:** Once the user starts or resumes open-ended project
work, keep executing useful authorized work until the user explicitly stops,
pauses or ends that work. Checkpoints, summaries and commits are progress, not
completion. Apply the final-answer gate in Continuation and Stopping below.

**Standing authority:** Independently scope and complete reversible local
implementation, compatible design choices, bounded synthetic unit fixtures,
required tests, documentation, checkpoint commits and periodic normal upstream
pushes within the agreed plan. Choose recommended defaults and record rationale;
do not ask for routine planning/testing approval or a finish/continue vote.
This supersedes historical routine approval wording, not protected limits,
exhausted experiments or missing qualification evidence. Fresh bounded local
source-recovery and unit/regression checks are delegated even when historical
routine test accounting is missing; preserve unknown attempts, not approval gates.

## Project

micro_classifier builds a Jev-like **robot decision module**: an STM32N6 board
(N657: Cortex-M55 with the Neural-ART NPU) that attaches to a host robot, first
a ground rover and later a mini-drone. On every tick it answers a fixed
catalogue of typed questions (`choice`, `noul`, `score`) with probability
distributions. The active rover pilot is rules-first; a small INT8 student and
distillation from open teachers remain longer-term work, not current capability.
The host's own controller keeps actuation, inner loops, interlocks, and fail-safes.

## Current Work

Read [REVIEW.md][review] §473 for closing arithmetic report extent and intact472 archival;
§472 records detached integration closure and intact471 archival;
§471 records detached receipt-history preflight and intact470 archival;
§470 records nested receipt-history extent and intact469 archival;
§469 records retained integration extent and intact468 archival;
§468 records shared dynamics cache preflight and intact466-467 archival;
§467 records owning intake receipt segment extent;
§466 records intact463-465 archival;
§465 records integration receipt segment extent;
§464 records receipt segment extent before copying and hashing;
§463 records intact458-462 archival;
§462 records initial-source and startup pending cache preflight;
§461 records motion snapshot pending cache preflight;
§460 records intact453-457 archival;
§459 records goal owner pending cache preflight;
§458 records owning intake pending cache preflight;
§457 records ToF acquisition pending cache preflight;
§456 records intact448-452 archival;
§455 records delivered ToF pending cache preflight;
§454 records detached initial observation preflight;
§453 records shared live motion word preflight;
§452 records intact443-447 archival;
§451 records live motion observation preflight;
§450 records startup cached observation preflight;
§449 records initial retention cached observation preflight;
§448 records intact438-442 archival;
§447 records initial-source cached observation preflight;
§446 records owning intake cached observation preflight;
§445 records cached integration observation preflight;
§444 records intact433-437 archival;
§443 records cached receipt observation preflight;
§442 records cached ToF observation preflight;
§441 records cached goal observation preflight;
§440 records intact428-432 archival;
§439 records dynamics configuration preflight;
§438 records native dynamics scalar preflight;
§437 records observation metadata preflight;
§436 records observation array preflight;
§435 records bounded dynamics position sampling;
§434 records intact423-427 archival;
§433 records bounded raw goal words before dynamics copying;
§432 records original goal retention owner identities;
§431 records shared goal owner layout preflight;
§430 records original goal delivery ownership;
§429 records final goal retention history prehash validation;
§428 records goal delivery history prehash validation;
§427 records intact418-422 archival;
§426 records final delivery base-history prehash validation;
§425 records final retention history prehash validation;
§424 records prevalidation before retention staging;
§423 records closing delivery trace prehash validation;
§422 records closing native history preflight and intact413-417;
§421 records closed current-ToF original owner contexts;
§420 records closed current-ToF original history joins;
§419 records closed original native-ToF history sampling;
§418 records intact408-412 archival and named input blockers;
§417 records closed post-observation history consumption;
§416 records closed owning intake history-root hashes;
§415 records bounded receipt-history prehash validation;
§414 records the prior named-queue evidence/tool blockers;
§413 records closed initial retention owner-word joins;
§412 records intact initial-source/receipt/startup topic relocation;
§411 records closed opted-in request owner preflight;
§410 records closed initial-source/startup owner preflight;
§409 records closed receipt/integration snapshot owner preflight;
§408 records intact403-407 checkpoint archival;
§407 records owning intake owner prevalidation;
§406 records bounded native recorder owner poses;
§405 records closed current-ToF post-observation owners;
§404 records closed native goal owner prevalidation;
§403 records intact401-402/original bibliography archival;
§402 records codec State prevalidation before owner copying;
§401 records intact399-400 archival;
§400 records fixed State-frame prehash extent checks;
§399 records intact397-398 archival;
§398 records closed native-ToF snapshot owner layouts;
§397 records intact395-396 archival;
§396 records closed native-ToF retention owner layouts;
§395 records intact391-394 archival and current evidence limits;
§394 records closed post-native receipt/pending copies;
§393 records closed owning intake original/final sampling;
§392 records intact386-390 archival and remaining evidence;
§391 records closed conditional startup receipt cache identity;
§390 records closed live request receipt cache identity;
§389 records closed composed native/receipt cache identities;
§388 records the former source-queue evidence assessment;
§387 records closed native goal dynamics sampling;
§386 records intact source-pipeline checkpoint archival;
§385 records closed fresh native-ToF retention sampling;
§384 records closed native-ToF delivery report work;
§383 records closed current native-ToF source sampling;
§382 records the former remaining evidence assessment;
§381 records intact consumer/remainder checkpoint archival;
§380 records intact native-word topic relocation;
§379 records closed current heading remainder joins;
§378 records supplied heading remainder discrepancies;
§377 records closed live request consumer epochs;
§376 records intact heading/receipt checkpoint archival;
§375 records closed owning receipt epoch identities;
§374 records closed default native epoch identities;
§373 records closed current heading-offset reports;
§372 records intact normalization checkpoint archival;
§371 records supplied heading shift/return residuals;
§370 records actual heading operand retention;
§369 records closed actual-consumed quotient joins;
§368 records intact initial-source checkpoint archival;
§367 records actual consumed-divisor retention;
§366 records closed current later-period comparisons;
§365 records supplied normalization division residuals;
§364 records intact initial-source checkpoint archival;
§363 records conditional owned initial-rest startup;
§362 records bounded retained initial-source reading;
§361 records bounded initial-source retention;
§360 records intact source/consumer checkpoint archival;
§359 records closed setup-report consumer metadata;
§358 records closed actual initial-tick/setup correspondence;
§357 records intact motion checkpoint archival;
§356 records actual intake closing-observation repairs;
§355 records the prior remaining acceptance-blocker assessment;
§354 records closed live-receipt owned request joins;
§353 records intact motion/goal checkpoint archival;
§352 records native integration closing-observation repairs;
§351 records closed current segment-selection reports;
§350 records supplied unrounded segment-count comparisons;
§349 records closed current receipt interval reports;
§348 records intact reviewed goal-expression archival;
§347 records intact motion-word contract relocation;
§346 records supplied captured-interval division residuals;
§345 records closed current receipt motion-update reports;
§344 records intact goal-delivery checkpoint archival;
§343 records supplied target/yaw clipping correspondence;
§342 records supplied pre-integration speed-update residuals;
§341 records matched retained goal storage reports;
§340 records supplied native/stored goal-word correspondence;
§339 records matched retained native goal expression reports;
§338 records intact goal ownership checkpoint archival;
§337 records supplied native goal expression residuals;
§336 records current-state review, goal boundary repairs
and the completed matched goal delta gate;
§335 preserves the former WIP and explicit pause;
§334 records intact native goal prerequisite archival;
§333 records supplied-word native goal delta discrepancies;
§332 records closed default-off native goal delivery;
§331 records exact retained native goal matching;
§330 records default-off native goal recorder retention;
§329 records typed bounded native goal history;
§328 records intact prerequisite checkpoint archival;
§327 records closed native goal acquisition intake;
§326 records native goal acquisition pairing;
§325 records cold native goal source capture;
§324 records completed matched selected/storage reports;
§323 records completed supplied selected/storage residuals;
§322 records intact retention/delivery checkpoint archival;
§321 records completed matched clip/select reports;
§320 records completed supplied-word clip/select diagnostics;
§319 records completed matched dropout reports;
§318 records completed supplied-word dropout-mask diagnostics;
§317 records the completed matched noise-addition reports;
§316 records intact postprocessing checkpoint/topic relocation;
§315 records the completed supplied-word noise-addition report;
§314 records completed postprocessing delivery publication;
§313 records the completed retained-postprocessing matcher;
§312 records the completed postprocessing retention checkpoint;
§311 preserves the cloud harness handoff/restart prompt;
§310 records completed typed postprocessing history and the former WIP gate;
§309 covers bounded closed postprocessing intake;
§308 covers intact product/pitch checkpoint archival;
§307 covers fresh native postprocessing acquisition
pairing; §306 covers cold return-postprocessing capture and distinct receivers;
§305 covers matched native final-up copy reports;
§304 covers supplied-word native final-up copies;
§303 covers intact direction checkpoint archival;
§302 covers matched native yaw-expression reports;
§301 covers supplied-word native yaw expressions;
§300 covers matched native pitch-expression reports;
§299 covers intact ray checkpoint archival;
§298 covers supplied-word pitch-rotation expressions;
§297 covers matched native direction product reports;
§296 covers supplied-word direction product discrepancies;
§295 covers closed delivered/pending direction publication;
§294 covers bounded retained native direction joins;
§293 covers recorder-owned native direction history;
§292 covers the lossless 281-285 checkpoint archive;
§291 covers typed direction-history validation;
§290 covers bounded closed direction-source intake;
§289 covers intact ray-source design relocation to chapter01;
§288 covers fresh ray-to-ToF acquisition pairing,
§287 covers cold pairing and fixture-only repairs,
§286 covers native ray generation and lossless 276-280 archive,
§285 wall/cylinder boundary words and
closing-order repair, §284 cap-square residuals and stable-source
revalidation, §283 cap-relative,
§282 covers guarded top division and the lossless 271-275 archive, §281 scalar offset,
§278 the NF1 relocation to chapter04 and §274 the cylinder topic in chapter05.
§§231-287
retain wall correspondence and the complete
cold cylinder/acquisition trace with their arithmetic/ownership limits.
§§226-228 preserve earlier interrupted/unknown
attempts and autonomous routine-recovery authority; those attempts are not refunded.
Default-off <=8-record postprocessing recorder retention and its required gate
are complete. Retained matching and delivered/pending publication are complete.
Standalone supplied-word noise-addition diagnostics and their required gate are
complete; retained additive reports and their required gate are complete.
Standalone dropout comparison/mask diagnostics and their gate are complete;
retained mask reports and their required gate are complete.
Standalone clip/select word diagnostics and their required gate are complete;
retained clip/select joins and their required gate are complete.
Whole311-315 checkpoints are archived with historical anchors and ledgers.
Whole316-320 checkpoints are archived with historical anchors and ledgers.
Whole321-325 checkpoints are archived with historical anchors and ledgers.
Whole326-330 checkpoints are archived with historical anchors and ledgers.
Whole331-335 checkpoints are archived with historical anchors and ledgers.
Whole336-340 checkpoints are archived with historical anchors and ledgers.
Whole341-345 checkpoints are archived with historical anchors and ledgers.
Whole346-350 checkpoints are archived with historical anchors and ledgers.
Supplied selected/storage residuals and their required gate are complete.
Retained storage report joins and their required gate are complete.
Native integration source/arithmetic already exists and must not be duplicated.
Cold goal consumed-operand/storage capture, actual acquisition pairing,
closed intake and typed bounded history with their required gates are complete.
Default-off <=8-record goal retention and its required gate are complete;
retained exact goal matching and its required gate are complete;
closed default-off latency0 delivered-goal publication and its gate are complete.
Pending goal publication is unsupported by frozen C1's zero-latency domain;
supplied-word native goal delta discrepancies and their gate are complete.
Matched retained goal delta reports and their required gate are complete after
reviewed final-source closure and malformed-owner guards. The historical §335
root position remains spent/aborted; recovered pytest output is not chain-exit
evidence. The fresh review gate passed5412 tests plus the known QDQ xfail.
The user's fresh actual continuation resumes the ordered queue. Supplied-word
native goal expressions and closed matched retained reports with their gates
are complete; supplied native/stored goal-word correspondence and its gate are
complete; default-off matched retained storage reports and their gate are
complete. Q2 supplied pre-integration speed-update residuals and their gate are
complete using existing receipt operands, not a new capture or uniform bound.
Supplied target/yaw clipping correspondence and its gate are complete; equal
values with different zero words retain unresolved selection ties.
Default-off current receipt clipping/speed-update reports and their gate are
complete; final producer observations precede sampled words and final owner
closure. Supplied captured-interval quotient residuals and their gate are
complete, using observed planned segments without segment-selection prediction.
The supplied/current motion-word and native integration-source contracts now
live in chapter06; chapter01 and chapter04 retain their old anchors as reading
links, without NF1 premise adoption.
Independent default-off current receipt interval reports and their gate are
complete, including combined motion-update mode; original/closing report work
precedes final producer/owner closure. Supplied unrounded segment-selection
comparisons and their gate are complete; native count4 versus reference3 is
a retained word discrepancy, not a native rounding or segment-count law.
Independent default-off current segment-selection reports and their gate are
complete across all report combinations. The existing0.1 program divisor is
explicitly labeled, not an invented captured intermediate; reference counts
are not trimmed to the128-recorded-segment cap. Native integration source and
arithmetic readers now sample after their last observation and reject malformed
current owners; their fresh gate is complete, without new arithmetic stages.
Independent default-off live-receipt joins for owned request preparation and
rechecking are complete, including original/closing metadata/request copies
and malformed current-owner rejection. They do not qualify source/clock,
permit a command or alter existing fixture-only defaults.
Independent Q0-Q4 acceptance remains missing, but the renewed actual request
continues smaller compatible prerequisites. Q0's owning intake sampler now
observes before collecting original/closing pose/action/goal/profile words and
rejects malformed original/closing owners; its fresh gate is complete.
The prior§355 no-further-prerequisite conclusion is not a continuation stop.
Whole346-350 archival is complete.
Whole351-355 archival is complete. Strict opt-in actual initial-tick/setup source
Whole356-360 archival is complete. Strict opt-in actual initial-tick/setup source
correspondence and its required gate are complete, with original/closing producer
and owner RNG identities pinned. It is not a reset execution receipt, accepted
setup/geometry/source authority or permission. Its setup-report validator now
shares the unchanged named startup consumer predicate, including exact root,
reason and bounded integer work. Its required gate is complete. Next trace
conditional owned initial-source consumption without inventing acceptance.
Frozen C1 ToF latency2 leaves no delivered capture at tick0; it is not goal's
odometry latency0. Explicit opt-in <=1 initial source snapshot retention and its
required gate are complete, including exact deduplication and pinned epoch joins.
Bounded retained initial-source reading and its recovery gate are complete,
including original/copy/current/closing source and pinned epoch joins. The first
interrupted root remains spent/unknown. Conditional owned initial-rest startup and its required gate are complete at
ticks2-3 using actual retained initial source, current receipt State/frame history
and delivered C1 event. Copied consumer evidence/capture bindings close after
consumer work. Explicit point/error/history assumptions remain unaccepted;
all flags false and guard UNKNOWN. No current initial-tick claim, reset receipt,
one-use or setup/source/geometry/clock acceptance follows. Next reassess the
remaining named source/coverage/native-error prerequisites without duplicating
completed reports or inventing bounds.
Supplied angle/divisor/normalized-argument quotient residuals and their required
gate are complete. The diagnostic divisor is caller-supplied, not source or pi
evidence by itself; later period_rad is not earlier capture. Existing ten-stage
integration diagnostics remain unchanged and unsupported normalization/pi/sinc
obligations are not adopted. Independent default-off current later-period
comparisons and their required gate are complete, with original/copy/closing/final
bindings and pinned RNG identities. The comparison labels the later heading-period
word, not the earlier consumed sinc divisor. Actual earlier sinc_divisor_rad
retention and its required gate are complete at the owning expression, without new
arithmetic or changed output words. Closed source/arithmetic readers retain the
finite builtin word; missing/unsupported words stay unknown. Independent default-off
actual-consumed quotient joins and their required gate are complete, including
combined later-period mode. Both groups close after the last producer sample with
pinned epochs; default output and ten-stage arithmetic remain unchanged.
Actual heading shift/return offset retention and its required gate are complete,
including missing/nonfinite words and current/closing joins. The two pi reads
remain distinct source words; no modulo/rounding/pi law follows. Single-mode
normalization digest ceilings are restored; only combined mode uses the larger cap.
Bounded supplied heading shift/return residuals and their recovery gate are complete.
The first root timeout remains spent/unknown; recovery used the same360s deadline.
Canonical nonfinite inputs block both ratios with zero arithmetic. Next add the
separate default-off actual-source heading join and its required gate are complete,
including all report combinations and original/copy/closing/final bindings.
The ten-stage report and pi/modulo/floor/error obligations remain unchanged.
Default native source/arithmetic closing epoch repairs and their required gate are
complete. Coordinated producer/owner/cache reference replacement and between-read
replacement stay unknown; matching RNG states are not original object identity.
Owning receipt closing epoch repairs and their required gate are complete across
all eight report combinations, including malformed producer rejection before
attribute access. Original producer references are pinned; coordinated equal-state
owner/cache replacement stays unknown without partial reports.
Opt-in live request preparation/rechecking original producer and RNG epoch joins
and their required gate are complete across both reads and after the closing
reader returns. The failed initial recheck pin placement is preserved with its
repair; default-off fixture behavior and work limits remain unchanged.
The receipt helper's conditional initial-startup consumer already pins producer,
RNG and retained-source identities through closing reads and consumer work;
its unchanged green gate was not separately rerun.
Bounded supplied heading remainder residuals and their required gate are complete,
including raw nonfinite unknowns and exact large integer quotients. This compares
caller words to an ideal rational remainder, not a native modulo/pi/error law.
Independent default-off current-source remainder joins and their required gate
are complete across all sixteen report combinations, with original/copy/closing/
final ownership checks. Prior per-family ceilings and ten-stage output are
unchanged; only all four groups use the new combined work cap.
Native-word/source topic relocation is complete with24 historical anchors;
the NF1 body is intact and no premise or authority is adopted. Whole376-380
archival is complete, including source/consumer repros, arithmetic boundaries and
both relocation failures/repairs.
The fresh actual continuation found and repaired a current native-ToF source
closing gap. Both observations precede source-word sampling; closing dynamics
words are refreshed after the last native intake without another observation.
Original cache/RNG/odometry/owner identities close after that work. Malformed
producers stay unknown;2 observations/2 intakes/64 digests and all false flags remain.
The late-intake pose regression and its repair are retained. The corresponding
delivered/pending reader now observes after all closing scalar reports, preflights
archive layout before dependent validators, then closes pending words and final
delivered words/mask/sensor tick. Existing observation/matcher/queue/digest limits
remain; the preflight repair and failed cadence fixture are retained.
Fresh acquisition retention now pins original epochs/owner content before its
first observation, observes before both intake groups and refreshes final dynamics
after closing source work. Eight original-epoch/final native/trace repros and its
required gate are complete; dedup/trim/gap and per-family work limits are unchanged.
Whole381-385 archival is complete, retaining the former blocker assessment,
fresh continuation/pause/resume and source/delivery/retention repros and repairs.
The same Q1 goal-source trace now pins retention epochs before its first
observation and shares post-observation native dynamics sampling in retention/
delivery. Closing dynamics refresh follows the last native intake without another
observation/intake/digest;20 epoch/native-action repros and its gate are complete.
All eight report combinations/defaults and prior goal controls remain unchanged.
The fresh actual continuation traced receipt/native integration composition and
closed equal-word cache replacement across reads. The native source reader pins
its original receipt cache across both receipt reads; the arithmetic wrapper pins
both native and receipt caches across source reads and its intervening probe.
Four false-availability repros and their required gate are complete; no source/
observation/report/math call or work ceiling changed. Current words and cache
identity are still not source authority, propagated error or permission.
Opt-in live request preparation/rechecking now also pin the original receipt cache
before the first receipt read through consumer work and after the closing reader
returns. Six initial/between/closing equal-word replacement repros and their gate
are complete; defaults and existing read/digest/work limits are unchanged.
Conditional owned initial-startup now pins the same original receipt cache across
both receipt reads/consumer work. Three equal-word cache replacement repros and
its gate are complete; eight observations/256 digests and all prior work limits
remain. Whole386-390 archival is complete, including former evidence assessments,
failed archival checking, source/cache repros, repairs and spent ledgers. All six
live-receipt helper calls are within the repaired startup/prepare/recheck consumers.
The fresh actual continuation closes owning intake's original/final sampling.
Existing owner/producer/RNG/binding pins now precede its first observation; native
dynamics words are collected after receipt/native work from that same observation.
Nine first-epoch and two post-intake pose/action repros and their gate are complete;
two observations and existing intake/digest/math work ceilings remain.
Combined intake now copies receipt words/flags and pending sample words/masks after
the native intake. Four late receipt/queue repros and their required gate are
complete; only existing blocks moved, without another read/copy/digest or changed
ceiling. Whole391-394 archival is complete, preserving original/final intake
repros, repairs, failed formatting/documentation and spent ledgers. Fresh native-ToF
retention now rejects malformed initial producer/current tuple/State/frame/dynamics
before sampling and closing tuple/State layouts before owner serialization.
Ten failing controls and their required gate are complete; prior30 controls and
per-family work ceilings remain. Timing cache joins were already closed; no timing
logic changed. Whole395-396 archival is complete with historical anchors and the
topic target intact. Timing-delivery history/output joins are already closed.
Current/delivered snapshot owner prevalidation now rejects malformed tuple/tick/
State/frame/dynamics before indexing/dict access or source work. Twelve failing
controls and54 prior controls pass. The first360s root timeout remains spent/
unknown; one fresh same360s recovery passes6273 tests plus the known QDQ xfail.
Whole397-398 archival is complete, including the checker failure and spent timeout/
same-deadline recovery. Initial/closing ToF retention and current/delivered snapshot
owners now require the existing fixed State-frame extent before owner hashing.
Eight short/long prehash repros and their required gate are complete; root6281 plus
the known QDQ xfail. No new frame encoding/copy/digest/read, wire or physical bound.
Whole399-400 archival is complete with historical anchors and the topic target intact.
Nested ToF owner State fields now pass the existing codec predicate before asdict,
including closing retention;16 short/long ages/vector controls and the required gate
are complete. Root6297 plus known QDQ xfail; no extra copies/encodings/source reads.
Whole401-402 and the original source bibliography are archived intact. The root
keeps every historical heading and its used reference definitions with unchanged
first-definition behavior; this is organization, not new evidence or scope.
Corresponding native goal original/closing State/frame preflight and its required
gate are complete in retention/delivery. The existing codec predicate and92-byte
wire ABI reject unsupported owners before copying/hashing; no new encoding,
intake or digest. The tuple-only test assertion repair is retained; root6321/
known QDQ1 xfail passed. Disabled no-op/eight report combinations/zero-latency
domain remain unchanged. Next trace remaining named source consumers without
inventing independent acceptance inputs or duplicating completed reports.
Current-ToF snapshot ownership now pins the already validated current tuple and
revalidates State before original/closing copies after observations. Six focused
and74 prior controls plus root6327/known QDQ1 xfail passed. The two failed delivery
fixture attempts are retained; delivery already checks companion State/frame and
is unchanged. No new intake/digest/copy/encoding or false-flag/domain change.
Owner-pose serialization on all five native retain/current/delivery paths now
requires the existing native ndarray/three-coordinate C1 shape before hashing,
including closing in-place resize. One shared guard reuses the unchanged C1
array predicate; no new native read/report stage or general binder change.
Its25 prehash controls and94 prior controls passed; root6352/known QDQ1 xfail
passed. No geometry/error/source/clock/one-use/admission claim follows.
Owning intake now validates current tuple/tick layout before indexing and actual
State/fixed frame extent/codec/pose before original/closing serialization.
Legitimate current=None startup and existing staged ideal-view fixture work remain.
The Step keyword and over-broad fixture prohibition failures are retained;21
focused/69 prior controls and root6373/known QDQ1 xfail passed. No new sample,
encoding, copy, digest or native report stage.
Whole403-407 archival preserves complete failures/ledgers/evidence limits and
five historical root headings; five topic targets rebase without new evidence.
Receipt/source/arithmetic snapshot owners now share exact current tuple/tick,
actual State/codec, fixed92-byte frame and native pose preflight before original/
closing copying/hashing. Forty-eight reproduced controls and266 prior controls
passed; root6421/known QDQ1 xfail passed. The initial counter error is retained:
receipt/source/arithmetic make2/6/12 observations, not2/2/4, because source readers
include receipt reads. Existing native intakes/digest ceilings/report combinations,
ten-stage output and missing-current behavior are unchanged.
Initial, retained-initial and conditional startup owner serialization now reuses
the same current-owner preflight before original/closing copies/hashes. Its24
red/repaired controls and86 prior controls passed; root6445/known QDQ1 xfail
passed. Startup's closing control mutates after the final retained reader returns,
so its own outer binder is exercised. No new sample/setup/consumer/copy/hash call,
domain, assumption or qualification.
Opted-in request/recheck owner metadata now closes before original/closing event
serialization, including after both receipt readers return. Known unsupported
metadata returns explicit unknown without partial request/receipt publication;
default fixture-only branches and error behavior are conserved. Twenty-one
failing/repaired controls and94 prior controls passed; root6466/known QDQ1 xfail
passed after the retained test-only Ruff C408 repair and necessary fresh gate.
No new receipt/native read, request preparation, copy or digest.
Ten complete initial-source/receipt/startup contracts now live in chapter06;
chapter01 retains historical anchors/reading links. Exact257-line bodies, both
inverse layouts, first-definition meanings and24 scoped references passed;
chapter01/06 are2482/874 lines. Tested411 code hashes are unchanged; no suite rerun.
Initial retention now closes actual current metadata and source pose/State/frame
words after the final snapshot reader returns, before final binding/epoch checks.
Ten fresh/dedup repros and86 prior controls passed; root6476/known QDQ1 xfail
passed. A changed native State word can retain the same encoded frame; the
existing exact source-owner helper distinguishes it. Its bounded State/frame
reconstruction and two owner-word digests fit the unchanged84-digest ceiling;
two reads/four observations/two setup audits and all flags remain unchanged.
The fresh actual continuation found a concrete receipt-history prehash gap after
the §414 reassessment. Receipt/source/arithmetic readers now validate exact list/
<=8 root extent before original/closing owner hashes; receipt entry rejects arrays
before truth-testing. The full history checker still requires nonempty history.
Twelve red/repaired controls and280 prior controls passed; root6488/known QDQ1
xfail passed. Existing calls, source words, missing-source behavior and work caps
are unchanged. The owning intake now runs its unchanged configured-history extent
guard inside both owner bindings, including after the final observation.
Six late-root repros passed after repair, plus68 prior controls and root6494/known
QDQ1 xfail. No sampling/copy/digest call or work cap changed. The same receipt
branch now reuses the shared root guard after its first observation and before
truth-testing/copying. Four red/repaired controls and74 prior controls passed;
root6498/known QDQ1 xfail passed. Empty dicts previously reached copying; this
NumPy runtime rejects empty-array truth before copying, not through the named
history predicate. Default-off source AST and all prior test AST are unchanged.
Whole408-412 checkpoints are now archived intact: exact144-line body, all five
historical headings, three inverse layouts, four topic targets and148 original
first-definition meanings passed. Root review shrank981->864 lines before the
new note;417 tested code hashes remain unchanged and no suite was rerun.
The fresh continuation found the native-ToF retainer's base acquisition-history
fingerprint followed its first observation/intake, allowing changed older entries
to become the accepted baseline. Moving that existing digest before the first
observation closes four fresh/dedup deletion/word repros;140 prior controls and
root6502/known QDQ1 xfail passed. No digest/sample/intake/cap change follows.
Current-ToF snapshots now independently preflight/fingerprint the same archive
before their first observation. Two false-availability repros and74 prior controls
plus root6504/known QDQ1 xfail passed. Delivered snapshots already establish their
owner/history bindings before observing and are unchanged. Existing2 observations/
intakes/64 digests remain. Current-ToF owner content is now fingerprinted before
the first producer sample, after independent retained-source layout validation.
Two context/profile repros and89 prior controls plus root6506/known QDQ1 xfail
passed. The first related run exposed four delayed fail-fast rejections; a shared
mid-read current-owner preflight preserves those checks without extra digests or
observations. The same current reader now revalidates history layout after the
last observation/intake and before closing hashes. Two prehash repros,66 prior
controls and root6508/known QDQ1 xfail passed. No copy/digest/sample/intake or work
cap changed. Whole413-417 is archived intact:156-line body, two inverse layouts,
five historical anchors/four topic targets and154 prior first-definition meanings.
The fresh continuation closed five optional delivery histories' prehash gap.
Their individual closing hashes now follow the unchanged late compound owner
preflight. Ten controls cover final observation and final dynamics refresh; the
first repair's lost late guard and its spent gate are retained in §423. Final
related366 and root6518/known QDQ1 xfail passed. Retention now also checks all
six live trace histories after the first intake and before staging copies.
The original and closing owner checks stay in place; six regressions and
root6524/known QDQ1 xfail passed. The closing owner check now also precedes the
retainer's two individual live-history hashes after the final dynamics refresh.
Two regressions,142 prior controls and root6526/known QDQ1 xfail passed.
Default delivery now also preflights base acquisition history after the final
refresh before hashing it. Timing already rejected the corresponding mutation.
Eleven focused and318 related controls and root6527/known QDQ1 xfail passed.
Whole418-422 is archived intact:157-line body, two inverse layouts, five
historical root headings, four topic targets and160 prior first-definition meanings.
Native goal delivery now checks its live retained history before both owner
fingerprints, including after the final refresh. Two regressions,473 prior
controls and root6529/known QDQ1 xfail passed.
Goal retention now checks live history after that refresh before owner hashing.
Two fresh/repeat regressions,475 prior controls and root6531/known QDQ1 xfail passed.
Goal delivery now fingerprints prevalidated ownership before its first native
intake and observation, retaining the midpoint and closing guards.
Four focused,475 prior controls and root6533/known QDQ1 xfail passed.
Goal retention and delivery now reject non-integer current ticks before closing
owner serialization. Focused26, related455 and root6535/known QDQ1 xfail passed.
Goal retention now pins the original current tuple and dynamics object across
producer work. Two regressions,481 related and root6537/known QDQ1 xfail passed.
Shared dynamics sampling now validates raw goal words before copying them.
Two regressions,546 related and root6539/known QDQ1 xfail passed.
Whole423-427 is archived intact:110-line body, two inverse layouts, five
historical root headings, four topic targets and166 prior first-definition meanings.
Shared dynamics sampling now checks position extent and numeric array type
before conversion. Four focused,546 related and root6541/known QDQ1 xfail passed.
Shared dynamics sampling also checks observation array shape and dtype before
hashing. Two focused,593 related and root6543/known QDQ1 xfail passed.
It now rejects extra observation keys and nonscalar metadata before hashing.
Four focused,593 related and root6545/known QDQ1 xfail passed.
Shared dynamics sampling rejects nonnumeric native yaw/action types before
conversion. Two focused,597 related and root6547/known QDQ1 xfail passed.
The observation preflight checks the actual Config before accessing its fields.
Six focused,595 related and root6549/known QDQ1 xfail passed.
Whole428-432 is archived intact:94-line body, two inverse layouts, five
historical root headings, five topic targets and172 prior first-definition meanings.
Goal retention and delivery now check cached observation layout before original,
mid-read and closing hashes. Six focused,601 related and root6555/known QDQ1 xfail passed.
No work cap or qualification change.
Actual independent Q0-Q4 inputs remain absent;
ST tools are not on PATH and licence/board/protected studies stay user-side or
deferred. A concrete issue or independent evidence can resume local work, not
qualification by metadata or another duplicate report.
The actual S1-S5/Q0-Q5 packet still lacks independent Q0-Q4 inputs;
no matching-hash guard/executor follows.
ST tools remain absent from PATH; licence/board and protected studies stay
user-side/deferred. New actual evidence or a concrete compatible issue can resume
local work; no qualification or usable command is admitted.
Named-queue reassessment against design §§1/2/12 and the Q0-Q5 packet still lacks
independent
Q0 setup/source/return/coverage, Q1 propagated state, Q2 uniform native/accumulated
error, Q3 pose/range/time/transform and Q4 clock/application/one-use/predecessor
evidence remain absent. Guard/executor composition cannot bypass those inputs.
stedgeai/stm32ai/STM32_Programmer_CLI are not on PATH; host/Arm compilers exist,
but licence/board and protected studies remain user-side/deferred. This is a
current input/authority blocker, not routine approval/accounting or a permanent
no-prerequisite claim. A concrete compatible issue or independent evidence can
resume local work; no qualification or usable command is admitted.
Rechecked named Q0-Q4 evidence remains absent; ST tools are not on PATH. Autonomy
does not supply qualification or protected study/hardware authority.
Q0 accepted setup/source/return/
coverage, Q1 propagated state error, Q2 full-domain native/accumulated error,
Q3 pose/range/time/native-transform enclosures and Q4 qualified clock/application/
one-use/receipt/predecessor evidence remain absent. Current words and hashes do not
replace those inputs. ST tools are not on PATH; licence/board work stays user-side.
Qualification studies, SC18, learned/D4 work and changed bounds/domains remain
protected or deferred. This is not an old pause, missing routine test approval
or a permanent assertion that no prerequisite can ever exist. A new concrete
source/consumer issue or independent evidence can resume compatible local work
under standing authority; no command is admitted.
Whole366-370 checkpoints are archived intact, including the archival checker/
premature sequencing failure and the single-mode digest-ceiling oversight/repair.
Whole371-375 checkpoints are archived intact, including the spent/unknown root
timeout, same-deadline recovery and native/receipt closing repros and repairs.
Whole361-365 checkpoint archival is complete, including failed fixtures and the
spent/unknown interrupted root; historical anchors and topic links remain intact.
Named source/setup auditors and motion/registration/request consumers remain
conditional; uniform native error, pose/range transform, clock/application/
one-use and admitted predecessor evidence is not accepted.
Do not duplicate completed integration/floor/goal reports. Preserve consumed
coefficients and observed delta without trig/noise/geometry/error adoption;
do not repeat unchanged green gates.
Preserve
original/closing native/RNG/profile/pose/input/stored-word/mask joins; retain
raw unsupported/nonfinite source as unknown without noise-law adoption.
Floor division reports already
exist and are not a new task;
raw unsupported/nonfinite source stays unknown. Preserve supplied
operands, raw nonfinite unknowns, identity/closing checks and unresolved word ties.
Squared-norm correspondence alone is not ray geometry or numerical qualification.
Preserve unresolved equal-value/different-word
ties; matching words do not prove geometry, coverage or error.
§§181-191 record workflow, clocks and source ownership. The Q0-Q5
source/named-consumer qualification packet (§180) is prepared, not adopted.
All qualification/admission flags remain false; no usable command is admitted.

Continue this ordered queue, deriving smaller compatible prerequisites when a
release gate is blocked:

1. Retain bounded native ToF acquisition, recorder and delivery correspondence
  as source prerequisites, without adopting numerical or physical bounds. Nominal
  ticks or observed timing do not qualify clocks, one-use execution or permission.
2. Advance independently supported setup/source/coverage/error/timing evidence
  for the named consumers; implement compatible offline prerequisites without
  inventing bounds, accepting claims or starting protected studies.
3. Compose supported request/guard/executor dependencies only as their evidence
  permits. No actuation or admitted predecessor chain follows from matching hashes.

ST licence/tools and board readiness remain user-side blockers; learned work,
D4 task-quality runs and general audits/SC18 remain deferred. Detailed milestones,
failed checks, approvals and spent ledgers belong in [DESIGN.md][design] §12 and
dated [REVIEW.md][review] sections, not here. Replace this short state as it changes.
The fresh continuation resumes the queue. Committed documents are portable;
local logs/editor memory/tools/environments are not assumed available.

## Start With Context

- Read Current Work and the newest relevant checkpoint in [REVIEW.md][review]
  before continuing implementation. The root review and [DESIGN.md][design]
  are reading maps; follow chapter links for the relevant numbered scope.
  Use design §§1, 2 and 12 for active scope and gates; consult §4 for teacher
  work, §6 for numerical/architecture work and the relevant §7 subsection for
  sensor, coverage and data work. Do not load entire archives for routine work.
- Check the actual worktree, nearby implementation/tests and applicable local
  instructions. Preserve user changes, including editor settings and untracked
  files. After an interrupted tool call, verify its outcome before repeating it.
- Verify selected environments, cached files, pinned revisions, available tools
  and resource budgets rather than assuming they survived a restart. Reuse
  existing caches and environments; do not duplicate downloads or checkouts.
- Distinguish proposed, approved, implemented, tested, integrated and measured
  work. A historical approval or completed bounded run is not renewed permission.
  Apply the current standing authority to new routine local work; do not treat
  older per-checkpoint approval wording as a reason to ask again or stop.

## Documentation Audience

- [README.md][readme] is the public introduction: capabilities, maturity limits,
  documentation links and licensing. Do not add routine progress updates, test
  counts, commit histories or session handovers. This rule does not request a
  separate cleanup of existing documentation.
- Keep architecture, accepted requirements, contracts and rationale in
  the chapters indexed by [DESIGN.md][design]. Keep changing status,
  discussions, commands/results, failed-check history, evidence limits and
  next-session handovers in dated
  [REVIEW.md][review] updates. Older numbered checkpoints live in its linked
  archives. Preserve failures, approvals, spent ledgers and evidence limits;
  moving a record does not renew authority or qualify its claims.
- Keep root reading maps short; archive whole older sections before exceeding
  about 1,000 lines. Keep individual archive/topic files around 2,500 lines or
  less, rebase local links and preserve historical anchors. New checkpoint
  notes should state the change, actual checks/failures, limits and next action
  without repeating the full prior handoff. These are organization targets,
  not experiment budgets or product requirements.
- Use [.devcontainer/README.md][container-guide] for reusable environment/setup
  instructions. Use existing documents rather than creating new Markdown files
  unless asked. Use reference-style links and check their targets.
- Keep stable workflow rules here. Replace Current Work and task summaries as
  they change rather than appending more historical checkpoints to this file.

## Work Independently

- Do not invoke `vscode_askQuestions` or equivalent agent-controlled
  questionnaire/choice dialogs. Do not spawn subagents unless explicitly requested.
- Own planning and execution: choose the first useful unblocked task, record its
  finite scope/resource budget and exit condition, implement, verify, checkpoint,
  then start the next useful authorized action in the same turn. Missing routine
  planning/testing approval is not a blocker.
- Assistant-written proposals and test plans are not permission gates for work
  already delegated. Do not replace implementation with repeated documentation-
  only budget proposals, approval requests or checkpoint reports. Record the
  bounded routine plan and execute it within the same work slice.
- At material checkpoints or new evidence, reassess the plan and priority queue;
  update compatible choices independently. Apply delivered user corrections
  promptly. Reviews are not new permission gates or reasons for repeated audits.
- Form a falsifiable local hypothesis from the owning code and a nearby test.
  Make the smallest useful edit and immediately run a focused check before
  expanding scope. Reuse existing tests/helpers and avoid unrelated cleanup.
- For an isolated blocker, name the missing evidence, authority, tool or input,
  retain the conservative state, prepare useful prerequisites and continue other
  unblocked work. Diagnose tool failures and use supported alternatives.
- Give concise progress updates: what changed, what was verified and what
  remains. Do not manufacture work merely to keep a turn alive.

## Continuation and Stopping

- Treat an open-ended continuation as active across checkpoints, commits,
  pushes, progress reports, tool notifications, reloads and context compaction.
  Completing one task does not complete the session or require another continue.
- Do not end active work with a routine permission/finish vote. An assistant-
  imposed planning gate or missing routine test ledger is not an all-path blocker;
  use the recovery rules below and take the next useful authorized action.
- During open-ended work, process new user messages delivered by the platform
  before the next slice; apply the newest compatible instructions. Do not claim
  inbox polling or message checks with unavailable tools.
- Determine current user intent from actual user instructions, not an assistant
  recap, generated conversation summary, quoted transcript or historical stop.
  These are context, not new user commands. A recap describing an old pause or
  summary-only request cannot end a subsequently resumed continuation. If the
  latest actual request is unavailable, recover it from available session
  history before deciding to stop; do not invent a stop instruction.
- An explicit current stop, pause or finish request takes priority. Stop safely
  without confirmation; cancel or contain owned work, retain evidence and leave
  a concise handoff. Do not start another slice or delay for unrelated checks,
  commits/pushes or a finish vote. Quoted stop words or a request to stop
  interrupting are not requests to pause project work.
- Stop/finish instructions apply to the current work, not future continued
  sessions. A fresh continue or changed task requires evaluating the latest
  request; do not carry an old finish permission across checkpoints, later turns
  or context loss. After a pause, a status question or terminal notification is
  not permission to resume implementation.
- Respect explicit task boundaries. A standalone documentation-only request,
  review or proposal is not permission to start separate implementation or
  collect data. During an already active continuation, handle a side request
  within its scope, then resume the existing authorized queue unless the user
  explicitly pauses, replaces or limits that continuation. An explicit "only
  update documentation", "review only" or equivalent limit must be honored;
  standing authority never expands that limit or authorizes protected actions.
- Use commentary for checkpoint reports and side-request results during active
  continuation, then execute the next concrete action. Do not issue a checkpoint
  final answer, offer to continue or leave an authorized next step for another turn.
- Use event-based waiting only when a supported tool is actually waiting for
  authorized work or required input; follow its notification protocol. Do not
  use sleep loops, repeated polling, dummy jobs or invented work to keep a turn
  alive. Instructions alone cannot provide background message monitoring.
- If every useful in-scope path is genuinely blocked, or platform/tool limits
  prevent execution, report the exact constraint and pending action; do not
  pretend to remain active. Missing admission evidence, an exhausted experiment
  or an isolated blocker does not end compatible prerequisite work. Do not evade
  protected limits or invent work to avoid stopping.

**Final-answer gate.** Before ending a turn, verify one of these applies:

- The user explicitly stopped, paused or ended the active work.
- A standalone bounded request is complete, with no active continuation to resume,
  or the user explicitly replaced the continuation with that bounded request.
- Every useful authorized path is genuinely blocked after checking compatible
  prerequisites and the remaining agreed queue; identify the precise blockers.
- A higher-priority safety requirement or an actual platform/tool limit prevents
  further work; state the concrete constraint without claiming to remain active.

Otherwise, the next action must be useful authorized work, not a final answer.
A clean worktree, green gate, checkpoint, commit, push, recap or completed side
request is not a stopping reason. This is an instruction-level behavior rule,
not a guarantee of unlimited execution or background message monitoring.

## Verification and Commits

- Prefer bounded synthetic fixtures for routine arithmetic, codec and integration
  checks. Default tests need neither downloads nor a GPU; no implicit inference,
  task-data collection or training.
- Required focused/regression checks for meaningful source changes are delegated.
  Record finite fixture/query counts, attempt/resource caps and failure/cleanup
  plans before execution. Count failures/aborts; retain tolerances, hard work
  limits and per-family controls.
- If historical routine test accounting is missing, mark interrupted/unknown
  attempts as spent/unknown and start a fresh bounded revalidation ledger under
  standing authority. Run the necessary focused and root checks without another
  approval request; never infer a past pass, refund old attempts or treat a new
  ledger as qualification evidence. This does not reopen protected experiments
  or override an explicit user-imposed execution ceiling.
- Distinguish explicit user-imposed hard caps and protected experiment budgets
  from assistant-selected routine test plans. For the latter, diagnose a failure
  before any rerun and document a narrowly revised finite plan when a necessary
  repair or required verification needs it. Do not repeatedly reset budgets for
  unchanged failures, rerun unchanged successful gates, relax fixture/work/safety
  limits or manufacture a new scope to evade a protected cap.
- Old spent experiment ledgers remain historical and are not refunded. Existing
  fixtures may run as unchanged controls in the required regression gate for a
  new source change; this does not authorize standalone old experiments, extra
  study runs or deferred audits. A substantive repair permits another necessary
  check within the recorded scope. Increasing an explicit user-imposed hard cap
  or protected experiment budget still needs explicit authority.
- After a substantive edit, run the cheapest behavior-scoped check first. Before
  each source checkpoint commit, run focused checks for the changed behavior and
  the default gate from the repository root:

```sh
python -m pytest -q && ruff check . && git diff --check
```

- Run `ruff format --check <changed Python files>` as well. Leave unrelated
  formatting alone, including `.devcontainer/smoke.py`.
- For C/native/runtime changes, ensure the applicable Python/C parity, host,
  ASan/UBSan and Cortex-M55 hard-float compilation controls actually ran; use
  the existing interface tests and documented opt-in gates. Report skips and
  missing prerequisites accurately. Host tests and Arm objects are not linked
  firmware, board execution, stack/memory-fit or task-quality evidence.
- Do not relax tolerances, assertions, deadlines, token/tensor bounds or safety
  checks for green results. Diagnose before rerunning; substantive repairs permit
  necessary checks within scope. Preserve the known transformer QDQ xfail.
- Do not rerun an unchanged successful gate merely for reassurance. For
  documentation/instruction-only changes, validate scoped content, references,
  local targets and whitespace; state that the code suite was not rerun.
- Scoped checkpoint commits and periodic normal pushes are authorized. Commit
  meaningful verified increments. Review the diff and stage only checkpoint
  files; never include or discard unrelated user work.
- Keep the remote reasonably synchronized by pushing verified checkpoints
  periodically through the current branch's configured upstream, without an
  approval prompt. Check the worktree, branch and tracking state first. If the
  remote advanced, fetch and reconcile conservatively without discarding either
  history; validate affected work before a normal push. Do not force-push,
  silently change remotes or alter credentials/security settings to make it work.
- If synchronization is blocked, retain the local commits, record the precise
  cause/pending action and continue other useful work. Diagnose before retrying;
  do not invent credentials or repeatedly retry an unchanged failed push.
- Use Conventional Commit subjects (`type(scope): imperative summary`, with scope
  optional) and a real bullet body. Branch creation, force-pushes and history
  rewriting still need explicit direction. Never revert another person's changes.

## Protected Boundaries

**Protected boundaries.** Where fresh explicit authorization is absent, choose
not to take the protected action; record the reason and recommended next action
without an approval questionnaire, and continue other useful in-scope work:

- Changes to accepted product requirements, question meanings, metric or
  safety thresholds, frozen interface contracts or physical safety behavior.
  A compatible implementation choice is delegated; a new product/safety
  requirement is not silently adopted by choosing a convenient default.
- New study episodes, task labels/imports, dataset/cohort/split acceptance,
  teacher labeling, training, outcome-driven tuning, or uncertainty/risk-policy
  adoption not covered by a current explicit authorization. Exhausted protected
  run approvals stay exhausted; synthetic unit fixtures are not task data.
- Running third-party model code at a revision the user has not approved; new
  model experiments beyond the exact approved runtime/resource/run scope; new
  or upgraded dependencies; changes to `.devcontainer`.
- Downloads other than approved model revisions, and any download that would
  leave less than about 20 GB of free disk space.
- Deleting files or data you did not create, force-pushing/rewriting git history,
  creating branches/changing remotes, and external account setup, licences,
  payments or contacting people. Normal checkpoint pushes using the existing
  configured upstream are covered by the standing authority above.
- Hardware access/integration or privileged/host-level changes outside the
  agreed scope. Do not alter clocks, networking, TLS/security or privilege
  settings as a testing workaround.

Never convert autonomy into evidence: source qualification, numerical proof,
task quality and physical clearance still require their actual acceptance
evidence; hashes, passing fixtures and agent defaults are not substitutes.
Prepare authorized prerequisites and record the precise protected action,
expected evidence, resource budget and cleanup plan for a future user directive.
Never request passwords, tokens or other secrets. Do not reopen settled choices
without new evidence or a changed claim/domain. After three failed approaches
to the same problem, retain the failures, mark the blocker and switch to other
useful in-scope work rather than repeating the same attempt.

## Rules

- Evidence: cite primary sources and label estimates as estimates. Never present
  unmeasured fit, latency, or accuracy as fact. Scores from different Decision
  Index editions are not comparable.
- Third-party model code: pin/review the full revision and verify its manifest,
  selected environment and current exact run authority. Historical approvals do
  not renew runs. Record approvals/evidence in [REVIEW.md][review]; consult
  [DESIGN.md][design] §4 for teacher contracts and resource limits.
- Never use TypeSafe's hosted Jev outputs for training, labels or tuning,
  autotrust JEV models, or Crivo models for commercial work.
- Never use the GTX 1080 Ti (no BF16). Default RTX A3000 peak reserved GPU memory
  stays below about 11 GiB; normal 9B-class token budget is 2,048. Verify actual
  hardware before use and retain stricter experiment-specific caps. Serialize GPU jobs.
- Dependencies: without explicit authorization, keep the current environment
  and use installed tools. For an authorized dependency change, update
  `.devcontainer/requirements.in` and regenerate both hash locks with the commands in
  [.devcontainer/README.md](.devcontainer/README.md). Never disable TLS
  verification or `--require-hashes`.
- Keep weights, datasets, caches, and ST tools out of git; add ignore rules when
  creating such directories.
- On-device means on-device: never move inference to the host for a feature
  described as running on the module.
- Safety: the module only recommends. No design may let module output or
  silence stop a drone's motors in flight, and host fail-safes stay independent.
- Put Python code in the existing top-level packages by area (`interface/`,
  `sim/`, `teacher/`, `export/`, or an approved new area), C code in `firmware/`,
  and generated data in ignored directories. Reuse local conventions/helpers.
- Environment/setup: [.devcontainer/README.md][container-guide]. Verify selected
  tools/interpreters; the recorded default is Python 3.12 at `/opt/venv`, not an
  assumption that it survived a restart. Model, study and hardware commands are
  opt-in only under current protected authority; GPU-only tests skip without CUDA.

## Leave a Clear Handoff

- At meaningful checkpoints, add a dated [REVIEW.md][review] update with the
  actual change, commands/results, failed-check history, evidence limits,
  artifact retention/cleanup and next concrete action. Update accepted design
  decisions in [DESIGN.md][design] and the concise Current Work here.
- Keep raw logs for long-running authorized jobs in ignored directories. Run
  large-memory/GPU jobs serially, one GPU job at a time, and report measured
  resource use without presenting process counters as hardware guarantees.
- After a restart, verify file sizes/tails and live processes before repeating
  work. Preserve damaged and uncommitted versions before recovery; use bounded
  reads and summaries instead of whole-file diffs or historical log dumps.
  Never clear user/editor caches or attribute a crash to OOM without evidence.
- When the final-answer gate permits a handoff, include commit IDs, verification,
  remaining boundaries and worktree state. Never continue after a stop or pause.

[design]: DESIGN.md
[review]: REVIEW.md
[readme]: README.md
[container-guide]: .devcontainer/README.md
