# Deisseroth Semantic Fusion Neuroscience

NEUROSCIENCE
Conserved brain- wide emergence of emotional response
from sensory experience in humans and mice
Isaac Kauvar†, Ethan B. Richman†, Tony X. Liu† et al.
Full article and list of
author affiliations:
https://doi.org/10.1126/
science.adt3971
A B
Quantifying emotional response to aversive
stimulus in human and mouse subjects
Brain-wide activity screening using intracranial
electrical recording in human and mouse subjects
Provide repeated
air puffs to eye
Record eye closure
(reflexive & affective)
Verbal report of
subjective experience
C
Conserved dynamics underlying emergence of emotion from sensation
Fast
stimulus
broadcast
Typical intrinsic timescale
Emotional
state
Persistent brain-wide activity
With dissociative pharmacological modulation (ketamine):
Fast
Accelerated intrinsic timescale
stimulus
broadcast
Rapidly resolved brain-wide activity
INTRODUCTION: Emotional states are central to the human condition
in health and disease, yet the neural processes by which emotions
emerge from experience remain mysterious. In mammals, lasting
emotional responses may serve to integrate external and internal
information spread across the brain, to guide contextually appropri-
ate behaviors. We hypothesized that common structural and
functional constraints on sensory integration into emotional states
in the mammalian lineage could yield conserved dynamical
principles governing the establishment and maintenance of
emotional responses.
RATIONALE: To identify broadly conserved patterns of neural activity,
we first developed unbiased brain- wide activity screens spanning
widely divergent mammalian species. Specifically, we explored when,
where, and how emotional states emerge, using high- speed, invasive,
and global methods in human and mouse subjects carrying out the
same task. While recognizing and leveraging the value of obtaining
verbal descriptions of subjective emotional experience from human
subjects for this question, we also explicitly bridged human and
mouse systems with temporally precise affective behavioral
measures, clinically compatible pharmacological interventions, and
deep brain- spanning intracranial electrophysiological readouts,
designed to be similarly carried out in parallel in both human and
mouse subjects, to investigate conserved principles underlying the
emergence of lasting emotional states from brief sensory input.
RESULTS: We determined that sequences of air puffs, directed at the
cornea of human or mouse subjects, elicit both fast/reflexive and
sustained/affective eye closure behaviors; the latter (in both species)
is characterized by negative valence, persistence, generalization, and
ablation by the dissociative agent ketamine. We performed a
brain- wide neural activity screen of this temporally precise behav-
ioral response, using intracranial stereo- electroencephalography
(iEEG) in humans and multiprobe Neuropixels single- unit electro-
physiology in mice. This brain- wide screen revealed a biphasic
process in which emotionally salient sensory signals are swiftly
broadcast throughout the mammalian brain and directly followed
by a slower and widely distributed persistent signal. We discovered
that the persistent signal could be selectively and similarly blocked
by ketamine while preserving the fast sensory broadcast in both
species, and that emergence of a behaviorally defined emotional
state could be selectively blocked by this intervention. We found
that the accumulation and decay pattern of persistent population
neural activity was consistent with first-order system dynamics, and
that the dose- dependent pharmacological impact on the emotional
response could be well- modeled by varying a single decay timescale
parameter, with emotion- blunting dissociative drugs accelerating
the decay. We furthermore found (in both humans and mice) that
ketamine accelerated the intrinsic timescale of baseline spontaneous
activity and reduced brain- wide population coupling in networks
with puff-triggered persistent activity. Control experiments in mice
Corresponding authors: Karl Deisseroth (deissero@stanford.edu); Vivek Buch
(vpbuch@stanford.edu); Carolyn Rodriguez (cr2163@stanford.edu); Paul Nuyujukian

(23sciencemag@pn.stanford.edu) †These authors contributed equally to this work. Cite
this article as I. Kauvar et al., Science 388, eadt3971 (2025). DOI 10.1126/science.adt3971
Science 29 May 2025 933
Aversive
stimulus
Aversive
stimulus
Brain- wide emergence of emotional response in humans and mice. (A) A
repeatable, temporally precise, and cross- species measure of emotional response.
(B) Broad, fast, and spatially resolved neural activity mapping across species with
intracranial electrical recording. (C) The aversive stimulus signal is rapidly and widely
broadcast, and from this, a sustained and distributed emotional state emerges.
Ketamine selectively blocks the sustained response by accelerating the decay rate of
system dynamics.
with a neutral auditory stimulus (while operating on faster times-
cales than emotionally salient stimuli) revealed that the pharmaco-
logical effect of sharpening response dynamics and reducing
capacity to maintain persistent information across the brain was
generalizable, highlighting the importance of signal persistence in
the establishment of brain- wide responses.
CONCLUSION: We find that mammalian emotional states, in a
conserved pattern spanning divergent species, are integrated from
sensory experiences through persistent activity dynamics that can
be shaped by a global and tunable intrinsic timescale, akin to the
action of a piano sustain pedal. Functioning as a distributed neural
context, adaptive emotional states appear to depend upon brain-wide
mechanisms of signal persistence in specific networks.
Furthermore, consistent with our measurements of intrinsic
timescale modulation by clinically relevant intervention, aspects of
the etiology and treatment of certain neuropsychiatric disorders
may be governed by altered stability of brain states linked to
maladaptively fast or slow intrinsic timescales.
Downloaded from https://www.science.org at Stanford University on May 29, 2025Research aRticle
NEUROscieNce
Conserved brain- wide
emergence of emotional response
from sensory experience
in humans and mice
Isaac Kauvar1,2,3†, Ethan B. Richman1,2†, Tony X. Liu1,2†,
Chelsea Li4, Sam Vesuna1,5, Adelaida Chibukhchyan1,2
,
Lisa Yamada1,2,6, Adam Fogarty1,2,7, Ethan Solomon1,5
,
Eun Young Choi1,6, Leili Mortazavi8, Gustavo Chau Loo Kung2,9
,
Pavithra Mukunda1,5, Cephra Raja2, Dariana Gil- Hernández1,5
,
Kishandra Patron1,2, Xue Zhang5, Jacob Brawer5
,
Shenandoah Wrobel2, Zoe Lusk7, Dian Lyu7, Anish Mitra1,5
,
Laura Hack5,10, Liqun Luo11,12, Logan Grosenick13
,
Peter van Roessel1,5, Leanne M. Williams5,10,Boris D. Heifets1,14
,
Jaimie M. Henderson6, Jennifer A. McNab9
,
Carolyn I. Rodríguez1,5,10*, Vivek Buch1,6*, Paul Nuyujukian1,2,6,15*,
Karl Deisseroth1,2,5,12*
Emotional responses to sensory experience are central to the
human condition in health and disease. We hypothesized that
principles governing the emergence of emotion from sensation
might be discoverable through their conservation across the
mammalian lineage. We therefore designed a cross- species
neural activity screen, applicable to humans and mice,
combining precise affective behavioral measurements, clinical
medication administration, and brain- wide intracranial
electrophysiology. This screen revealed conserved biphasic
dynamics in which emotionally salient sensory signals are
swiftly broadcast throughout the brain and followed by a
characteristic persistent activity pattern. Medication- based
interventions that selectively blocked persistent dynamics
while preserving fast broadcast selectively inhibited emotional
responses in humans and mice. Mammalian emotion appears
to emerge as a specifically distributed neural context,

driven by persistent dynamics and shaped by a global
intrinsic timescale.
Human beings experience sensory- evoked emotional states that modu-
late behavior both adaptively and maladaptively. These emotional
responses are defined by exhibiting (i) behavioral, (ii) physiological,
and (iii) subjective components (1, 2). While subjective experience can
be assessed using human- specific social communication, affective be-
haviors that comprise the external displays of an emotional response
can also be observed and characterized across diverse animal species,
with shared properties including scalability, persistence, valence, and
generalization (2–10). Emotional states that integrate rich information
to shape behavior may be especially complex in the mammalian lineage,
supported by the distinctive size and structure of the mammalian brain.
Large brains with distributed mapping of perception, cognition,
and action are well- suited to organize and encode diverse information,
but the same scale and complexity may pose difficulties for the rapid
integration of available information to generate adaptive behavior. It
is unclear from a brain- wide systems perspective how neural processes
for establishing and maintaining a fully integrated and informed emo-
tional state may operate on fast neurophysiological and cognitive timescales.
Moreover, beyond this basic science perspective, clinical relevance
of these processes is substantial since diverse psychiatric disorders
involve altered emotional responses.
Recent advances using high- speed invasive and brain- wide neural
recording in laboratory animals have revealed that internal states
relevant to primary survival drives (such as hunger and thirst) can
shape brain- wide neural activity and guide behavior by acting as a
distributed neural context (11–17). However, these studies did not ad-
dress the emergence of emotional states. Thus, we sought to explore
when and where emotional states emerge using similarly high- speed,
invasive, and global methods while recognizing that given the subjec-
tive quality of emotion, deep insight may also require obtaining verbal
reports from human experimental participants. We therefore explicitly
bridged mouse and human systems by defining temporally precise
affective behavioral measures, clinically compatible pharmacological
interventions, and deep brain- spanning intracranial electrophysiologi-
cal readouts, which could all be similarly carried out in parallel in both
human beings and mice, to investigate conserved principles underly-
ing the emergence of lasting emotional states from brief sensory input.
Patterns observed in these global neural activity screens, from species
separated evolutionarily by many tens of millions of years, could have
the potential to reveal conserved and ancestral solutions to the chal-
lenge of manifesting emotional states within the complex and distrib-
uted mammalian brain.
Precisely timed affective behavior in mice and humans
We first sought to define a precise and quantifiable behavioral assay
that would capture the fast- timescale onset of an emotional state, and
that would be comparably controllable across species from humans to
mice. We identified a puff of air directed at the cornea (eyepuff) as a
candidate stimulus with critical features including clinical safety, tem-
poral precision, and repeatability. Eyepuffs are innately aversive stim-
uli across species (18–21) and evoke broad cortical neural responses
in mice (11); moreover, these stimuli are temporally delimited, pre-
cisely targeted, compatible with head- fixed neural recording, and safe
to administer to human beings (forming part of standard ophthalmo-
logical assessment). Finally, the mammalian behavioral response to
an eyepuff (eye closure) is fast, scalable, repeatable, easily scored in
an automated manner, and similar between mice and humans; more-
over, the neural circuitry governing eyepuff-triggered reflexive eyeb-
links is well- mapped (22–25). We hypothesized that eyepuff stimuli of
sufficient intensity and duration would evoke a behavioral response
with fast reflexive but also persistent affective features, and that these
features could manifest in temporally separable neural activity pat-
terns. To test these hypotheses, we developed a protocol for adminis-
tering eyepuffs to human participants or mice (Fig. 1) under conditions
that would allow measurements of behavioral responses and brain-wide
screens for neural responses, as well as intervention with medica-
tions, in both cases (figs. S1A, S2A, and S3).
Under control conditions (during intravenous saline administra-
tion) in human participants (Fig. 1A), we observed a multiphasic
response to the eye puff (Fig. 1B), composed of a consistent and fast
1Human Neural Circuitry program, Stanford University, Stanford, CA, USA. 2Department of Bioengineering, Stanford University, Stanford, CA, USA. 3Graduate School of Education, Stanford
University, Stanford, CA, USA. 4Neurosciences Graduate Program, Stanford University, Stanford, CA, USA. 5Department of Psychiatry and Behavioral Sciences, Stanford University, Stanford,
CA USA. 6Department of Neurosurgery, Stanford University, Stanford, CA, USA. 7Department of Neurology and Neurological Sciences, Stanford, CA, USA. 8Department of Psychology,
Stanford University, Stanford, CA, USA. 9Department of Radiology, Stanford University, Stanford, CA, USA. 10Veterans Affairs Palo Alto Health Care System, Palo Alto, CA, USA. 11Department
of Biology, Stanford University, Stanford, CA, USA. 12Howard Hughes Medical Institute, Stanford University, Stanford, CA, USA. 13Department of Psychiatry, Weill Cornell Medicine, New York,

NY, USA. 14Department of Anesthesiology, Perioperative and Pain Medicine, Stanford University, Stanford, CA, USA. 15Department of Electrical Engineering, Stanford University, Stanford, CA,
USA. *Corresponding author. Email: deissero@ stanford. edu (K.D.); vpbuch@ stanford. edu (V.B.); cr2163@ stanford. edu (C.I.R.); 23sciencemag@pn.stanford.edu (P.N.) †These authors
contributed equally to this work.
Science 29 May 2025 1 of 20
Downloaded from https://www.science.org at Stanford University on May 29, 2025Research aRticle
B C
Eye closure
0 1
Saline
0
Trial
10
20
30
Ketamine
Trial
0
10
20
30
*
Eye closure
−1 0 1 2
Time (s)
Saline Ketamine
J
Ketamine
Trial
0
5
10
**
Saline puff descriptions:
“Very unpleasant.”
“It wasn’t comfortable.”
“Hard to keep eyes open.”
Ketamine puff descriptions:
“It wasn’t at all unpleasant.”
“The air puff was not unpleasant,
but more felt entertaining.”
“Less bothersome.”
Preinfusion
Sal. Ket. PCP
ns ** *
Eye closure
A
Human eyepuff assay
D E F
Human subject ID
1 2 3 4
Airpuffs
to eye
Camera
to record
eye closure
Verbal report of
subjective experience
1.0
0.8
0.6
0.4
0.2
0.0
Sal.
Ket.
Late eye closure
(normalized by early)
1.0
0.8
0.6
0.4
0.2
0.0
−1 0 1 2
Time (s)
G H I
Saline
−0.5 0.0 0.5 1.0 1.5
Time (s)
Mouse subject ID
K L
1 2 3 4 5
Mouse eyepuff assay
0
5
Airpuffs
to eye
Trial
10
1.0
0.8
0.6
0.4
0.2
0.0
Sal.
Ket.
Late eye closure
(normalized by early)
0.6
0.4
0.2
0.0

−0.2
Late eye closure
(normalized by early)
1.0
0.5
Camera
to record
eye closure
0.0
−1 0 1 2
Time (s)
M N O P Q
Saline
Ketamine
−1 0 1 2
Time (s)
PCP
−0.5 0.0 0.5 1.0 1.5
Time (s)
K/X
Saline Ketamine
Saline Ketamine PCP
Ketamine disrupts late (‘affective’) but not
early (‘reflexive’) response across species
1.0
1.0
1.0
1.0
Pre
Saline
Pre
Ketamine
Pre
PCP
Pre
K/X
Saline
Eye closure
0.5
0.5
0.5
0.5
Eyepuff onset Reflexive
eye closure
Affective
eye closure
0.0
0.0
0.0
0.0
Ketamine
0 20 40 60
Time (s)
0 20 40 60
Time (s)
0 20 40 60
Time (s)
0 20 40 60
Time (s)
Reflex
Eyepuff onset No affective
maintained
eye closure
Fig. 1. A cross- species measurement of rapidly evoked negative emotion. (A) Human eyepuff assay schematic. (B) Single-trial puff-aligned eye closure of example
human participant during saline infusion or (C) ketamine infusion (0.5 mg/kg intravenous over 40 min) and (D) summarized across trials (mean ± SEM vertical dashed
line, airpuff onset; horizontal bar, airpuff duration; dashed box, time window of interest corresponding to late eye closure, 0.3 to 0.8 s after airpuff onset). (E) Late eye
closure, normalized by early eye closure (0.1 to 0.2 s after airpuff onset), decreases during ketamine (n = 4 human participants; each color represents a participant,
mean ± SEM across trials). (F) Participants’ descriptions of experiences during eyepuff assay with saline or ketamine infusion. (G) Mouse eyepuff assay schematic.
(H) Single- trial eye closure of example mouse during saline infusion and (I) ketamine infusion and (J) summarized across trials (mean ± SEM vertical dashed line, airpuff
onset; horizontal bar, airpuff duration; dashed box, time window of interest corresponding to late eye closure, 0.3 to 0.8 s after airpuff onset). (K) Late eye closure,
normalized by early eye closure (0.1 to 0.2 s afterpuff onset), decreases during ketamine (n = 5 mice; each color represents one participant, mean ± SEM across trials).
(L) Effect of dissociative drugs ketamine (50 mg/kg) and PCP (20 mg/kg) on late, normalized by early, eye closure relative to preinfusion (n = 5 mice; bar height indicates
mean). (M) Eye closure across sequence of eight closely spaced puffs, with administration of (M) saline, (N) ketamine, (O) PCP, and (P) general anesthetic dose of
ketamine/xylazine cocktail (135 mg/kg ketamine with 15 mg/kg xylazine). (M) to (P) n = 5 mice, mean ± SEM (Q) Summary of ketamine’s cross- species impact on reflexive
and affective components of the eyepuff eye closure response. ns (not significant), P-
value ≥ 0.05, *P-
value < 0.05. **P-
value < 0.01. See table S3 for information on
statistical analyses and sample sizes. [(A) and (G) partially created with BioRender.com.]
(“early”) reflexive blink followed by a more variable and extended
(“late”) partial eye closure (fig. S1, B, C, and E). If the late eye closure
indeed could be considered an affective behavior corresponding to
an emotional response, we would predict that (i) human participants
would describe a negative emotional state evoked by the sequence
of eyepuffs and (ii) this described emotional state and the late eye
closure would se lectively be reduced by the dissociative medication
ketamine, which causes emotional blunting (26), without blocking
stimulus awareness.
We found that human participants described a response to the
sequence of eyepuffs during the saline (control) session that was
consistent with a negative emotional state, which includes properties
of valence, arousal, persistence, and generalization (2, 27). The partici-
pants self- reported displeasure (“unpleasant”) and arousal (“it made
me jump!”) (fig. S1F) and exhibited eye closure that extended beyond
the duration of the stimulus, consistent with the self- reporting of a
persistent state (Fig. 1, B, D, and F, and fig. S1, E and F). One partici-

pant (#1) exhibited substantial lacrimation in addition to persistent
eye closure, revealing a generalized behavioral response with mul-
tiple physiological dimensions. Additionally, we indeed found that
administration of ketamine diminished the eyepuff- triggered late eye
closure while preserving the early reflexive blink (Fig. 1, C to E, and
Science 29 May 2025 fig. S1, B and C), and subjective reports of the aversive quality of the
stimulus were largely abolished by ketamine without blocking aware-
ness of the eyepuffs (fig. S1F). Natural human response variability
was of value here: participants with the strongest ketamine effect on
the eye closure phenotype also reported greater impact of ketamine
on the subjective experience of the eyepuff (fig. S1, E and F; leftmost
columns versus rightmost). The response to the eyepuffs thus exhib-
ited affective features of an emotional response, which were abol-
ished by ketamine without blocking the reflexive stimulus response.
Ad ditionally, consistent with the hypothesized emotional blunting
mode of action of the medication, acute ketamine induced a dissocia-
tive state in these same participants as rigorously quantified (along-
side eyepuff administration) with the validated Clinician- Administered
Dissociative States Scale (CADSS) rating scale for human dissociation
(fig. S1D). Together, these observations align with our predictions,
revealing that eyepuffs evoke a negative emotional state and that the
late eye closure can be considered an affective behavior correspond-
ing to this emotional response.
We anticipated that this approach, by design, should be extendable
beyond human participants; we therefore developed a similar eyepuff
protocol for mice (Fig. 1G and fig. S2A). We found that the multiphasic
eye closure response observed in humans was also present in mouse
2 of 20
Downloaded from https://www.science.org at Stanford University on May 29, 2025behavior, and that dissociative drugs such as ketamine and phencycli-
dine [(PCP), uniquely enabled for mice] similarly reduced late but not
early eye closure (Fig. 1, H to L, and fig. S2, B to D). Since mice cannot
verbally convey internal emotional states, we relied instead on behav-
ioral criteria to assess how single negative- valence eyepuffs relate to
the induction of a longer- timescale emotional state. We measured
behavioral changes during and after repeated sequences of eyepuffs
in close succession, which was enabled by the increased number of
trials that were possible with mice relative to human participants
(because of clinical considerations). We found that late- phase eye clo-
sure in mice accumulated across a sequence of eyepuffs and decayed
slowly after the final eyepuff in the sequence (Fig. 1M), demonstrating
persistence (fig. S2E) and scalability (fig. S2, F and G). Using a separate
reward- based assay, we found that eyepuff sequences elicited a persis-
tent reduction in reward seeking (fig. S4), suggesting generalization
of the induced state across behaviors. These features and the similarity
between human and mouse eyepuff behavioral response suggested
that the late phase mouse behavior can be considered an affective
response corresponding to a negative valence internal emotional state.
For brevity, we hereafter refer to the late phase of eye closure as af-
fective and the early phase as reflexive, in both mice and humans.
Consistent with this interpretation, we found that under either of the
two dissociative agents, ketamine and PCP, reflexive eyeblinks re-
mained present but affective eye closure responses were greatly re-
duced in magnitude, did not accumulate, and did not persist following
the eyepuff series (Fig. 1, N and O). By contrast, general anesthesia,
achieved through addition of xylazine to ketamine (a common com-
bination treatment when general anesthesia is desired), abolished both
reflexive and affective responses (Fig. 1P). Dose-response investigation
showed that these robust dissociative effects begin around 35 mg/kg
ketamine and 10 mg/kg PCP (fig. S2, H to J), consistent with prior
work (28). Similarly consistent with prior dissociation assessments in
mice (28), buprenorphine and diazepam did not show the same discon-
nection of reflexive and affective eye closure (fig. S5, A to H). Eyepuff
results were repeatable across days (fig. S2, K and L) and generalized
across experimental conditions, including with different air pressures
(fig. S2, G and M) and in both male and female mice (fig. S2N). Mice
do not proactively close their eyes under these conditions and there-
fore this assay was not modulated by anticipation of the precise timing
of upcoming eyepuffs (fig. S2O).
A key barrier to studying neural dynamics of emotional states is
that most such states are not precisely replicable in timing and qual-
ity and thus identification of neural correlates lacks the statistical
power afforded by trial- averaging. The eyepuff assay, however, allows
for repeatedly and reliably evoking a well- timed and quantifiable
affective response corresponding to an emotional state. This affective
response can be selectively modulated through pharmacological in-

tervention while preserving a reflexive response that serves as a
crucial counterpoint (Fig. 1Q). The eyepuff assay may thus allow for
precise and robust mapping of relationships between neural activity
and emotional states across species. We therefore sought to track
neural dynamics during rapid- timescale emergence of emotional
states by applying the assay during high-speed, brain- wide neural
recording in both species.
Brain- wide activity screen during emergence of affect
in human beings
To seek neural activity patterns underlying the emergence of emotional
brain states that might be shared across mouse and human partici-
pants, we designed and conducted high temporal resolution brain-wide
activity screens in humans and mice. To guide the design and
application of the exploratory screens, we first formally verified the
importance of forebrain neural structures for the emergence of the
affective response, since affect would be expected to not rely solely on
peripheral nervous system or brainstem circuitry. We intercepted
Science 29 May 2025 Research aRticle
suprabulbar eyepuff- induced neural activity by inhibiting the mouse
ventral posteromedial (VPM) thalamus, which transmits ocular- tactile
input to the cortex (29), and found reduced affective eye closure rela-
tive to the reflexive response (fig. S6, A to J).
Next, to map central nervous system neural dynamics correspond-
ing to the stimulus- triggered affective response in human beings, we
sought a recording method for measurement of electrical activity at
high temporal resolution with brain- wide access (including in deep
subcortical regions). We additionally required spatial resolution ade-
quate for understanding local contributions to global patterns, as well
as suitability for many hours of electrical recording across behavioral
testing epochs, collection of verbal reports of subjective internal states,
administration of psychiatric rating scales, and measurements prior
to, during, and following administration of medications. The best
available technique meeting all of these criteria was intracranial
stereo- electroencephalography (iEEG) (30), for which we developed a
suitable protocol (Fig. 2A and fig. S7A). We completed a full assessment
(iEEG implantation followed by eyepuff administration alongside clinical
ratings in the presence and absence of continuous intravascular infusion
of the dissociative medication ketamine) in 14 human participants, of
which 7 met inclusion criteria (fig. S8, A and B, and Methods). An ad-
ditional cohort of 7 participants completed the study without the eyepuff
administration but with ketamine infusion (fig. S7B). All participants
received iEEG implantation with diverse electrode trajectories deter-
mined by individual clinical need (not study hypotheses), allowing an
unbiased brain- spanning activity screen to be assembled across the popu-
lation (Fig. 2B, fig. S7, C and D, and figs. S9, S10, and S11), with individual
responses aligned in time (to temporally precise events such as the
eyepuff) and aligned in space (to reference human anatomical maps).
As with the original non- iEEG- implanted outpatient participants
(Fig. 1), behavior in the independent iEEG- implanted inpatient cohort
displayed a multiphasic eyepuff response with a ketamine- elicited
selective decrease in the affective phase of the response (Fig. 2C and
fig. S8A); as expected, the iEEG- recorded participants also reported
fully reversible induction of dissociation (measured with the CADSS
instrument) during recordings (Fig. 2D). The simultaneous iEEG re-
cordings revealed local field potential (LFP) signals exhibiting clear
eyepuff- triggered event related potentials (ERPs) across the brain,
exemplified by the broadband voltage traces from insula and postero-
medial cortex (Fig. 2E). These ERPs could not be explained as neural
signatures of eyelid closure nor of unexpectedness of the sensory
stimulus: Despite similar magnitude of measured eyelid closure in
spontaneous versus puff- triggered eyeblinks, the ERP pattern was not seen
in spontaneous eyeblinks; further, the brain-wide eyepuff-triggered
response pattern was absent in response to an unexpected auditory
control, in which the eyepuff apparatus emitted the sound associated
with the puff of air but was directed away from the participant (figs.
S12, A to D, and S13D). Eyepuff- triggered LFPs across regions during
preinfusion and ketamine infusion periods revealed that the eyepuff
signal was rapidly and widely detectable across cortex (fig. S12E).
Ketamine was administered through a 40- min 0.5 mg/kg continu-
ous infusion, eliciting dissociation as characterized in fig. S14, A and
B, although we also explored either one- or two- step target- controlled
infusions and either one or two step boluses as in fig. S14, C and D.
We analyzed the brain- wide spectral effects of ketamine (fig. S15A)
by region (fig. S15B), by individual channel (fig. S15C), and by Yeo7
resting- state network, a standard human cortical parcellation based

on intrinsic functional connectivity (fig. S15D) (31). The time course
of spectral changes that we observed matched the time course of the
ketamine infusion pharmacokinetics (fig. S15, E and F), and these
spectral changes were distributed across the brain (fig. S15, G to I).
We observed a complex pattern of puff- triggered spectrotemporal
dynamics across recorded brain regions, with consistency observed
across participants (fig. S13, A to D and fig. S16, A and B). This brain-wide
response decreased in magnitude during ketamine infusion,
3 of 20
Downloaded from https://www.science.org at Stanford University on May 29, 2025Research aRticle
A B
Dissociation
** **
(CADSS)
20
10
0
Pre
Ket.
Post
G
Frequency (Hz)
100
75
50
25
0
E
Local field
potential (mV)
Subject
SD168
SD172
SD181
SD185
SD186
SD211
SD245
Example event related potentials
INS
PMC
0.1
0.0
−0.1
0.1
0.0
−0.1
−0.5 0.0 0.5 1.0
Time from puff onset (s)
−0.5 0.0 0.5 1.0
Brain-spanning neural response components
Factor 0 Factor 1 Factor 2
Factor 3 Factor 4 Factor 5
I
0 1 2 3 4 5
Factor #
Ketamine - Preinfusion
0 1
Z-score
Time from air puff onset (s)
-1
Change in neural response during ketamine
ns **** **** * ns ns
Air puff
Camera
Pre Ketamine Post
C D
Pre
1.0
Eye closure
Ket.
0.8
Post
0.6
0.4
0.2
Start ketamine infusion
0.0 0 0.5 1
Time (s)
F
Stack trial-averaged channel
spectrograms across subjects
Subject N
Channel C
...

