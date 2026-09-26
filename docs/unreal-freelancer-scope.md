# Scope of Work: Unreal Engine 5 Artist, DMB Hampton Coliseum NYE 1996 VR Demo

## 1. Project summary

We are building a proof of concept virtual reality recreation of about seven minutes of the Dave Matthews Band New Year's Eve show at Hampton Coliseum in Hampton, Virginia, on December 31, 1996. The demo starts at the midnight countdown (about 0:29 on circulating tapes) and runs straight into Tripping Billies (about 6:32), for roughly 7:01 in total.

The viewer stands at one fixed spot on the arena floor. They can turn, lean, crouch, and take a step or two in any direction (full six degrees of freedom head movement), but they cannot walk or teleport around the venue. The goal is photorealistic, real-time rendering on a PC VR headset.

This is a proof of concept. It should prove that the experience feels real and runs smoothly, not that every seat and every fixture in the building is finished.

## 2. The accuracy rule

This is the most important part of this document.

We are recreating a real night with real people. The only facts we currently hold are:

- The date, venue, and band.
- The approximate running times of the countdown and Tripping Billies on circulating tapes.
- Setlist notes saying Béla Fleck and the Flecktones and Paul McCandless were on stage for Tripping Billies, and that balloons dropped at midnight.

Everything else is unknown until it is confirmed from footage or photos. That includes who soloed when, lighting colors and cues, what anyone wore, stage layout, where people stood, which Flecktones members were present, and how the crowd behaved.

What this means for your work:

- Do not fill a gap with a guess, a typical Dave Matthews Band show from another night, or a detail from memory. If a detail is not confirmed in `docs/open-questions.md`, build it as a clearly swappable placeholder.
- Placeholders should be neutral and easy to replace: generic clothing materials, a neutral white or grey lighting state, grey-box stage props, and so on. Name them so they are obvious (for example `PH_Clothing_Performer03`).
- If you find a detail in footage that we have not logged, tell us with the source and timestamp. Do not build it until we have added it to the open questions list and marked it answered.
- Keep a short log of every reference you used and what it confirmed. This log is a deliverable (see section 10).

## 3. Reference material we will provide

- The chosen reference audio file, trimmed to the demo window, with its source noted (see Q-02, Q-04).
- Any video and still photos we can find of this show (Q-01, Q-06).
- The beat sheet (`docs/beat-sheet.md`), filled in second by second as answers come in.
- The open questions list (`docs/open-questions.md`) with answered items and their sources.
- A decision on the viewer's floor position (Q-15) and the fallback policy for unanswerable details (Q-54).
- The named target headset and PC specification (Q-52).

Some of this will arrive in stages. Early milestones are planned so you can start on the venue shell, tech setup, and systems before performer details are confirmed.

## 4. Venue

**Scope in:**

- The interior of Hampton Coliseum as it looked in December 1996, built to the level of detail that matters from the chosen floor position. Surfaces close to the viewer and in their main sightlines get the most detail. Far seating and ceiling can use lower detail, as long as nothing looks wrong at the headset's resolution.
- The seating bowl, roof structure, floor, and any hanging fixtures that footage or photos confirm (Q-11).
- The floor layout around the viewer: general admission, seats, barricade, and mixing position, as confirmed by footage (Q-12).
- Crowd occupancy in the stands to match what footage shows (Q-13).
- Any New Year's decorations confirmed by footage (Q-14).

**Scope out:**

- Exterior of the building.
- Concourses, backstage, and anything not visible from the viewer's position.

**Notes:**

- Modern photos of Hampton Coliseum may not reflect the 1996 interior. Use them for structure and scale only, and flag any difference you notice.
- Real world scale matters a lot in VR. Please build the venue to accurate real world dimensions from plans or measured references where possible, and tell us what you based the scale on.

## 5. Stage

**Scope in:**

- Stage deck, risers, backdrop, and set pieces as confirmed (Q-16).
- Instruments, amplifiers, microphone stands, drum kit, monitors, and cabling as confirmed (Q-18).
- Video screens, if any existed, and their content (Q-19).

Until those questions are answered, build the stage as a grey-box layout at a plausible arena scale so the performer and lighting work can proceed.

## 6. Lighting

**Scope in:**

- A lighting rig built to match the confirmed truss layout and fixture types (Q-20).
- Lighting cues keyed to the reference audio timeline, following the beat sheet's lighting column once it is filled in (Q-21, Q-23).
- House light behavior around midnight (Q-22).
- Atmospheric haze or fog only if confirmed (Q-24).
- Visible beams, which are central to how a 1990s arena show reads. Beam rendering has to hold up in stereo and at the target frame rate.

**Important:** we have no information about lighting colors or cue timing. Until the beat sheet lighting column is filled in, the lighting sequence must use a neutral placeholder state. Please build the cue system so that a color, intensity, position, or timing change is a data edit in a Level Sequence or data table, not a rebuild.

**Technical expectations:**

- Choose a lighting approach (for example Lumen, baked lighting, or a hybrid) that meets the frame rate target in section 11 on the target hardware. Tell us which approach you picked and why before you commit to it (milestone 1).
- If you use the DMX plugin or a fixture library, tell us which.

## 7. Performers (MetaHuman)

**Performers to build:**

- The five members of Dave Matthews Band as they appear on the footage (Q-25 to Q-29), plus anyone else confirmed on stage (Q-30).
- The Flecktones members confirmed as present (Q-31, Q-32).
- Paul McCandless (Q-33).

The final count depends on Q-30 and Q-31.

**Scope in:**

- A MetaHuman for each performer, matched to their 1996 appearance as closely as the confirmed references allow (face, hair, facial hair, build, height).
- Clothing and accessories per performer, only as confirmed in the open questions list. Until confirmed, use neutral placeholder clothing.
- Instruments held or played by each performer, as confirmed.
- Animation for the full demo window: playing that matches the audio closely enough to be believable in VR, lip sync for lead vocals, idle and stage movement, and entrances or exits (Q-34).
- Featured moments (solos, vocal passages) only as mapped in the beat sheet (Q-35 to Q-37). Do not stage a solo that has not been confirmed.

**Animation sources:** please propose your approach. Options include motion capture (performance capture of stand-ins), MetaHuman Animator or other facial capture, hand keyed animation, or a mix. Tell us the cost and quality trade off of each. Instrument playing, especially hands on strings, drums, and keys, is where believability will be won or lost, and we would like your recommendation on how far to take it for a proof of concept.

**Likeness:** these are real, identifiable people. Do not publish, post, or show any work in progress likenesses outside the project team. We are resolving likeness permissions separately (Q-50). If those permissions do not come through, the fallback may be non-identifying performers, so please keep likeness specific work (face sculpt, grooms) separate from the rig and animation so it can be swapped.

## 8. Crowd

**Scope in:**

- A crowd filling the floor and stands to the density shown on footage (Q-12, Q-13).
- Near crowd (roughly the people within a few meters of the viewer): higher detail characters with varied, era appropriate clothing as confirmed by footage (Q-43) and varied, non-repeating motion.
- Mid and far crowd: a lower cost solution (instanced, animated crowd, vertex animation, or similar) that still reads as a live, moving audience in VR.
- Behavior keyed to the timeline: the midnight moment (Q-44), the song (Q-45), and reactions to the balloons (Q-42).
- Crowd behavior should follow the beat sheet crowd column once filled in.

**Notes:**

- Near crowd members must not block the viewer's view of the stage in a way that makes the demo frustrating. Please propose a layout.
- Nobody in the crowd should resemble a real, identifiable person.

## 9. Balloon drop

**Scope in:**

- Balloons released at the confirmed time (Q-39), from the confirmed positions (Q-40), matching confirmed appearance and quantity (Q-41).
- Physically believable falling and drifting, collisions with the crowd and each other, balloons bounced by crowd members, and balloons coming to rest on the floor and stage (Q-42).
- Some balloons close to the viewer that the viewer's head can bump. A light touch reaction is enough. Hand interaction is out of scope for this proof of concept unless we agree otherwise.

**Technical expectations:** the drop is probably the single heaviest moment in the demo. Please propose how you will simulate it (for example Chaos physics, Niagara, or a baked simulation) while holding frame rate, and prototype it early (milestone 3).

## 10. Deliverables

1. **Packaged PC VR build** (Windows executable) that plays the full demo window from start to finish, in sync with the reference audio, on the target headset.
2. **Unreal Engine 5 project source**, with a clear folder structure, cleaned of unused assets, that opens and packages on our machine using the engine version we agree at kickoff.
3. **Master Level Sequence** that drives lighting, performer animation, crowd behavior, and the balloon drop from one timeline, with the reference audio on the track. The beat sheet timestamps should map directly to this timeline.
4. **Placeholder register**: a list of every placeholder in the build, what it is standing in for, and the open question ID it waits on.
5. **Reference log**: every reference source you used, what it confirmed, and where (file name and timestamp).
6. **Performance report**: frame timing captures from the target hardware at the heaviest moments (midnight, balloon drop, busiest lighting).
7. **Short build notes**: how to open, run, and package the project, and how to change a lighting cue or swap a placeholder.
8. **A flat 2D capture** of the full demo from the viewer's position, for people without a headset.

## 11. Technical requirements

- **Engine:** Unreal Engine 5. Exact version agreed at kickoff and not changed without agreement.
- **Platform:** Windows PC VR through OpenXR.
- **Target hardware:** one named headset and one named PC specification, to be confirmed by us (Q-52).
- **Frame rate:** hold the headset's native refresh rate (for example 90 Hz) at the heaviest moments on the target hardware, with no reprojection during normal playback. If this cannot be done at the level of realism we are asking for, tell us early and propose where to cut.
- **Viewer:** fixed standing position on the floor (Q-15). Six degrees of freedom head tracking. No locomotion. The viewer's physical play space is small, so nothing should break if the viewer takes a step in any direction or crouches.
- **Comfort:** no forced camera movement, no sudden bright flashes beyond what footage confirms, and a safe, comfortable brightness for strobes if any are confirmed (Q-24).
- **Audio:** play the reference audio in sync with the timeline. Whether audio is spatialized per instrument or played as a stereo mix depends on Q-48. Please set up the project so either is possible.
- **Start and end:** a simple start state (for example a hold on the venue before the countdown begins) and a clean end state after the song. No menus beyond what is needed to start playback.

## 12. Out of scope

- Any part of the show outside the demo window.
- Walking, teleporting, or changing the viewer's position.
- Hand tracking or controller interaction beyond starting playback.
- Multiplayer or social features.
- Standalone headset (non PC) builds.
- Venue exterior, backstage, and concourses.
- Audio restoration or mixing, unless agreed separately.
- Any detail not confirmed in the open questions list, beyond neutral placeholders.

## 13. Milestones

Dates and payment amounts to be agreed. The order is designed so work can start before performer and lighting details are confirmed.

1. **Tech setup and approach.** Project created on the agreed engine version, OpenXR working on the target headset, and a written proposal covering lighting approach, crowd approach, balloon approach, and performer animation approach with trade offs.
2. **Venue and stage grey box.** Venue shell at correct scale, viewer position, grey-box stage, reference audio on the master sequence, and a first frame timing check in the headset.
3. **Systems prototype.** Balloon drop prototype, crowd prototype (near and far), and lighting cue system driven from the sequence, all running together at the target frame rate with placeholder content.
4. **Performers first pass.** One performer fully built and animated for a short passage, to agree the quality bar before building the rest.
5. **Content pass.** All confirmed details applied: venue dressing, stage, performers, lighting cues, crowd behavior, balloon timing. Remaining placeholders listed in the placeholder register.
6. **Polish and delivery.** Performance tuning, bug fixing, final build, source, and all documents in section 10.

We would like to review in the headset at the end of each milestone.

## 14. What we need from you in your proposal

- Relevant portfolio work, especially real-time VR, MetaHuman, crowds, and concert or live event lighting.
- Your recommended approach for each area in milestone 1, and your main technical risks.
- An estimate by milestone, and how the estimate would change if the performer count goes up after Q-31 is answered.
- Your availability and preferred review cadence.
- Confirmation that you can keep all likeness and project material confidential.

## 15. Confidentiality and ownership

All reference material, likenesses, and project files are confidential. Ownership of the work, licensing of any third party assets, and credit will be set out in the contract. Please list any marketplace or third party assets you plan to use, with their licenses, before using them.
