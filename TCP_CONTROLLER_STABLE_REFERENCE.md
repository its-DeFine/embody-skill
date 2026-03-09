# TCP Controller Documentation (Stable Build Reference)

This reference is pinned to the currently deployed older/stable game build.
Do not assume compatibility with untested newer builds.

## Load/Save System
- `NEW.Character` - Creates a new character and resets all values back to default.
- `NAME.<Name>` - Sets character name.
- `BTN.Save` - Saves customization options.
- `Load.<Name>` - Loads a specific agent customization save.
- `Delete.<Name>` - Deletes a specific agent customization save.

## Metahuman Customization

### Presets
- `PRS.Masc`
- `PRS.Masc1`
- `PRS.Fem`
- `PRS.Fem1`

### Clothing
Format:
- `OF_Head_Torso_Legs_Feet_Back`

Head options:
- `NoHead`, `Halo`, `Astronaut`

Torso options:
- `LucyHalter1`, `LucyKimono`, `LucyBlackDress`, `LucyPopStar`, `LucyMaidDress`, `SarahDefaultDress`, `SarahKimono`, `SarahMaidDress`, `SarahPopStar`, `SpaceSuit`, `FemaleUnderArmor`, `FemaleArmor`, `LucyLivepeer`, `NoTop`, `MaleUnderArmor`, `ZachLongSleeve`, `HarryLongSleeve1`, `EmbodyPuffer`

Legs options:
- `LucyShorts1`, `FemaleJeans1`, `FemaleCargoPant1`, `HarryPants1`, `ZachPants2`, `MaleCargoPant1`, `FemaleCargoPant2`, `MaleCargoPant2`, `NoPants`

Feet options:
- `LucyBoots1`, `LucyStrapShoes1`, `FemaleLoafers`, `ZachShoes2`, `HarryShoes1`, `NoShoes`

Back options:
- `NoBack`, `Wings1`

### Hair Styles
- `HS.Default`
- `HS.Buzz`
- `HS.Crop`

### Skin
- `SKC.<float>`

### Makeup
Blusher:
- `MKUPF_BlusherMakeup_<float>`
- `MKUPC_BlusherMakeupColor_<r>_<g>_<b>`
- `MKUPF_BlusherMakeupIntensity_<float>`
- `MKUPF_BlusherMakeupRoughness_<float>`

Eye Makeup:
- `MKUPF_EyeMakeup_<float>`
- `MKUPF_EyeMakeupMetalness_<float>`
- `MKUPC_EyeMakeupPrimaryColor_<r>_<g>_<b>`
- `MKUPF_EyeMakeupRoughness_<float>`
- `MKUPF_EyeMakeupScattering_<float>`
- `MKUPC_EyeMakeupSecondaryColor_<r>_<g>_<b>`
- `MKUPF_EyeMakeupTransparency_<float>`

Foundation:
- `MKUPF_FoundationMakeup_<float>`
- `MKUPF_FoundationMakeupConcealerIntensity_<float>`
- `MKUPF_FoundationMakeupIntensity_<float>`
- `MKUPC_FoundationMakeupColor_<r>_<g>_<b>`

Lipstick:
- `MKUPF_Lipstick_<float>`
- `MKUPC_LipstickColor_<r>_<g>_<b>`
- `MKUPF_LipstickRoughness_<float>`
- `MKUPF_LipstickScattering_<float>`
- `MKUPF_LipstickTransparency_<float>`

Concealer:
- `MKUPC_ConcealerMakeupColor_<r>_<g>_<b>`

UV maps:
- `MKUPUV_EyeLipstickMask_<url>`
- `MKUPUV_FoundationBlusherMask_<url>`

### Bones
- `BNH.<float>`
- `BNC.<float>`
- `BNHD.<float>`
- `BNA.<float>`
- `BNAR.<float>`
- `BNL.<float>`
- `BNF.<float>`

### Hair Color
- `HCR.<float>`
- `HCG.<float>`
- `HCB.<float>`

### Hair Attributes (Floats)
- `HAIRF_Desat_<float>`
- `HAIRF_hairMelanin_<float>`
- `HAIRF_hairRedness_<float>`
- `HAIRF_HairRoughness_<float>`
- `HAIRF_HighlightsRootDistance_<float>`
- `HAIRF_LightAmount_<float>`
- `HAIRF_MelaninVariationFine_<float>`
- `HAIRF_MelaninVariationRough_<float>`
- `HAIRF_OpacityFar_<float>`
- `HAIRF_OpacityNear_<float>`
- `HAIRF_OpacityPowFar_<float>`
- `HAIRF_OpacityPowNear_<float>`
- `HAIRF_RoughnessVariation_<float>`
- `HAIRF_Spec0_<float>`
- `HAIRF_Spec1_<float>`
- `HAIRF_SpecEdge_<float>`
- `HAIRF_SpecFront_<float>`
- `HAIRF_WhiteAmount_<float>`
- `HAIRF_Highlights_<float>`
- `HAIRF_HighlightsBlending_<float>`
- `HAIRF_HighlightsIntensity_<float>`
- `HAIRF_HighlightsMelanin_<float>`
- `HAIRF_HighlightsMelaninFine_<float>`
- `HAIRF_HighlightsMelaninRough_<float>`
- `HAIRF_HighlightsRedness_<float>`
- `HAIRF_HighlightsVariationNumber_<float>`
- `HAIRF_Ombre_<float>`
- `HAIRF_OmbreContrast_<float>`
- `HAIRF_OmbreIntensity_<float>`
- `HAIRF_OmbreMelanin_<float>`
- `HAIRF_OmbreVariationFine_<float>`
- `HAIRF_OmbreVariationRough_<float>`
- `HAIRF_OmbreRedness_<float>`
- `HAIRF_OmbreShift_<float>`
- `HAIRF_Scraggle_<float>`
- `HAIRF_Region_<float>`
- `HAIRF_RegionMelanin_<float>`
- `HAIRF_RegionMelaninVariationFine_<float>`
- `HAIRF_RegionMelaninVariationRough_<float>`
- `HAIRF_RegionRedness_<float>`

### Hair Attributes (Colors)
- `HAIRC_HighlightshairDye_<r>_<g>_<b>`
- `HAIRC_OmbrehairDye_<r>_<g>_<b>`
- `HAIRC_RegionhairDye_<r>_<g>_<b>`

### Eyes
- `EC.<float>`
- `ES.<float>`

### Morph Targets
Format:
- `MT_<TargetName>_<float>`

Supported regions include: head, neck, ears, forehead, temples, eyebrows, eyes, nose, cheeks, lips, chin, jaw, horns.

## Camera System
- `View.Desktop`
- `View.Mobile`
- `CAMSHOT.Default`
- `CAMSHOT.ExtremeClose`
- `CAMSHOT.Close`
- `CAMSHOT.HighAngle`
- `CAMSHOT.LowAngle`
- `CAMSHOT.Medium`
- `CAMSHOT.MobileMedium`
- `CAMSHOT.WideShot`
- `CAMSHOT.MobileWideShot`
- `CAMSTREAM_X_Y_Z_RX_RY_RZ`
- `CAMLOC_X_Y_Z`
- `LOC_X_Y_Z`
- `ROT_X_Y_Z`

## Animation System

### Body Animations (Examples)
- `CONVO_Speaking`
- `CONVO_Despair`
- `CONVO_Dance`
- `CONVO_Dance2`
- `CONVO_StandingLaugh`
- `CONVO_FuriousSpeaking`
- `CONVO_SadTalk`
- `CONVO_SeriousTalk`
- `CONVO_WhisperLeft`
- `CONVO_WhisperRight`
- `CONVO_ListeningIdle`
- `CONVO_LeaningBar`
- `CONVO_BackAgainstWall`
- `CONVO_BenchLoop`
- `CONVO_RMSadGesture`
- `CONVO_RMMoveSad`
- `CONVO_RMLaughTalk`
- `CONVO_RMSeriousTalk`
- `CONVO_RMLeanRight`
- `CONVO_RMLeanLeft`

### Emotes
Emotion examples:
- `EMOTE_Angry`
- `EMOTE_Annoyed`
- `EMOTE_Confused`
- `EMOTE_Ponder`
- `EMOTE_Salute`

Action examples:
- `EMOTE_TellingSecret`
- `EMOTE_Bow`
- `EMOTE_CantHear`
- `EMOTE_ComeHereSeductive`
- `EMOTE_MakeItRain`
- `EMOTE_Wave`

Dance examples:
- `EMOTE_Dance2`
- `EMOTE_Grinding`

NSFW examples:
- `EMOTE_MiddleFinger`
- `EMOTE_FingerGunsViewer`
- `EMOTE_Jork`

## Post Processing Effects

### Bloom
- `BloomInt_<float>`
- `BloomMeth_Default`
- `BloomMeth_Convolution`
- `BloomSZE_<float>`

### Exposure
- `EXPOComp_<float>`
- `EXPOMinEV_<float>`
- `EXPOMaxEV_<float>`
- `EXPO_SpeedUp_<float>`
- `EXPO_SpeedDown_<float>`

### Chromatic Aberration
- `CHROME_Int_<float>`
- `CHROME_Offset_<float>`

### Color Grading
- `CG_TempType_WhiteBalance`
- `CG_TempType_ColorTemp`
- `CG_Temp_<float>`
- `CG_Tint_<float>`
- `CGG_*` families for global/shadows/midtones/highlights/misc/lens/film/dirt

### Other
- `VIG_<float>`
- `SHARP_<float>`
- `GRAIN_*`

## Lighting and 3D Assets

### Light Control
- `LIGHT_<Tag>_<X>_<Y>_<Z>`
- `LIGHTMOVE_<Tag>_<X>_<Y>_<Z>`

### Static Mesh Spawning
Format:
- `SPWN_<Tag>_<ObjectName>_<X>_<Y>_<Z>_<RX>_<RY>_<RZ>_<SX>_<SY>_<SZ>_<Extra>`

Related:
- `SPWNDEL_<Tag>`
- `SPWND`
- `SPWNMOVE_<Tag>_<X>_<Y>_<Z>_<RX>_<RY>_<RZ>_<SX>_<SY>_<SZ>`

Object examples include:
- `Bookshelf1`, `Bookshelf2`, `Chair1`, `BenchChair`, `Chair3`
- `Table1`, `Table2`, `Watercooler`, `TrashBin`, `Kettle`, `CoffeeMachine`
- `Microwave`, `Refrigerator1`, `Refrigerator2`, `Refrigerator3`
- `Mirror`, `Toilet`, `Locker`, `ComputerScreen`, `MountedTV`, `CCTV`
- `Planter*`, `Pot*`, `Tree*`

## Stream Playback and Background
- `m3u8_UI_<link>`
- `m3u8_UI_Plane`
- `m3u8_stop`
- `BACK_<link>`
- `BACK_`

## Game / Menu / Environment Legacy
- `QUIT.`
- Deprecated environment controls: `CLDS`, `CLDO`, `SNH`, `STRB`
- Deprecated menu controls: `MENU.`, `CMENU.`

## TTS

### BYOB
- `TTS_BYOB_<audio_path>_<mood>_<mood_intensity>`

### ElevenLabs
Setup format:
- `ElevenLabs=<API_KEY_PLACEHOLDER>=<VOICE_ID>=<VOICE_MODEL>=<AUDIO_FORMAT>`

Speak format:
- `TTS_ElevenLabs_<text>_<stability>_<similarity>_<style>_<speed>_<language_code>_<mood>_<mood_intensity>`

### Kokoro
Verified speak format:
- `TTS_Kokoro_Bella_Happy_0.7_<text>`

Validation order:
- Prove the command path with a visible camera command first, such as `CAMSHOT.Medium` or `CAMSHOT.Close`.
- If the camera command does not land, do not spend time tuning Kokoro text or timing yet.
- If commands stopped working after a game-only recreate, the script-runner may need recreation too because it shares the game network namespace and can drift after partial runtime resets.

Timing guidance:
- For normal use, send one Kokoro line at a time.
- Fixed `5s` spacing is a stress-test pattern only, not the recommended default.
- If you need multi-line delivery, use timing-aware queueing based on runtime signals rather than blind sleeps between commands.

Runtime interpretation:
- `Received audio buffer with N samples` means synthesis succeeded and audio reached the runtime.
- `Kokoro synthesis cancelled after inference` means that line truly failed at runtime.
- Lip-sync issues or audio buffer overflow can make a successful line feel skipped, so do not treat perceived silence as proof of synth failure without checking runtime evidence.

### NVIDIA Audio2Face
- `NVIDIA_<DestinationURL>_<API_KEY_PLACEHOLDER>_<FunctionID>`
- `TTS_NVIDIA_<wav_path>`

## Custom Outfits
- `CUSTOMFIT_<public_url>`

## Security Note
- Never store or transmit real provider API keys in this repo.
- Use placeholders in all docs and examples.
