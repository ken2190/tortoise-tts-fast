import os
from pathlib import Path
import gradio as gr

from tortoise.api import MODELS_DIR
from tortoise.inference import (
    infer_on_texts,
    run_and_save_tts,
    split_and_recombine_text,
)
from tortoise.utils.diffusion import SAMPLERS
from app_utils.funcs import (
    timeit,
    load_model,
    list_voices,
    load_voice_conditionings,
)

LATENT_MODES = [
    "Tortoise original (bad)",
    "average per 4.27s (broken on small files)",
    "average per voice file (broken on small files)",
]

def generate_samples(text, voice, preset, candidates, latent_averaging_mode, sampler, steps, seed,
                     voice_fixer, output_path, model_dir, high_vram, kv_cache, cond_free,
                     min_chars_to_split, produce_debug_state):

    conf = TortoiseConfig()
    conf.update(
        EXTRA_VOICES_DIR=extra_voices_dir,
        LOW_VRAM=not high_vram,
        AR_CHECKPOINT=ar_checkpoint,
        DIFF_CHECKPOINT=diff_checkpoint,
    )

    ar_checkpoint = None if ar_checkpoint[-4:] != ".pth" else ar_checkpoint
    diff_checkpoint = None if diff_checkpoint[-4:] != ".pth" else diff_checkpoint
    tts = load_model(model_dir, high_vram, kv_cache, ar_checkpoint, diff_checkpoint)

    os.makedirs(output_path, exist_ok=True)

    selected_voices = voice.split(",")
    results = []

    for k, selected_voice in enumerate(selected_voices):
        if "&" in selected_voice:
            voice_sel = selected_voice.split("&")
        else:
            voice_sel = [selected_voice]
        voice_samples, conditioning_latents = load_voice_conditionings(
            voice_sel, extra_voices_ls
        )

        voice_path = Path(os.path.join(output_path, selected_voice))

        with timeit(
            f"Generating {candidates} candidates for voice {selected_voice} (seed={seed})"
        ):
            nullable_kwargs = {
                k: v
                for k, v in zip(
                    ["sampler", "diffusion_iterations", "cond_free"],
                    [sampler, steps, cond_free],
                )
                if v is not None
            }

            def call_tts(text: str):
                return tts.tts_with_preset(
                    text,
                    k=candidates,
                    voice_samples=voice_samples,
                    conditioning_latents=conditioning_latents,
                    preset=preset,
                    use_deterministic_seed=seed,
                    return_deterministic_state=True,
                    cvvp_amount=0.0,
                    half=half,
                    latent_averaging_mode=LATENT_MODES.index(
                        latent_averaging_mode
                    ),
                    **nullable_kwargs,
                )

            if len(text) < min_chars_to_split:
                filepaths = run_and_save_tts(
                    call_tts,
                    text,
                    voice_path,
                    return_deterministic_state=True,
                    return_filepaths=True,
                    voicefixer=voice_fixer,
                )
                for i, fp in enumerate(filepaths):
                    results.append(fp)
            else:
                desired_length = int(min_chars_to_split)
                texts = split_and_recombine_text(
                    text, desired_length, desired_length + 100
                )
                filepaths = infer_on_texts(
                    call_tts,
                    texts,
                    voice_path,
                    return_deterministic_state=True,
                    return_filepaths=True,
                    lines_to_regen=set(range(len(texts))),
                    voicefixer=voice_fixer,
                )
                for i, fp in enumerate(filepaths):
                    results.append(fp)
    if produce_debug_state:
        """Debug states can be found in the output directory"""

    return results


def main(text, voice, preset, candidates, latent_averaging_mode, sampler, steps, seed,
         voice_fixer, output_path, model_dir, high_vram, kv_cache, cond_free,
         min_chars_to_split, produce_debug_state):

    results = generate_samples(text, voice, preset, candidates, latent_averaging_mode, sampler, steps, seed,
                               voice_fixer, output_path, model_dir, high_vram, kv_cache, cond_free,
                               min_chars_to_split, produce_debug_state)

    return results

input_text = gr.inputs.Textbox(label="Text", default="The expressiveness of autoregressive transformers is literally nuts! I absolutely adore them.")
input_voice = gr.inputs.Textbox(label="Voice", default="Voice 1")
input_preset = gr.inputs.Radio(["single_sample", "ultra_fast", "very_fast", "ultra_fast_old", "fast", "standard", "high_quality"], default="ultra_fast")
input_candidates = gr.inputs.Number(label="Candidates", default=3)
input_latent_averaging_mode = gr.inputs.Radio(LATENT_MODES, default=0)
input_sampler = gr.inputs.Radio(SAMPLERS, default=1)
input_steps = gr.inputs.Number(label="Steps", default=10)
input_seed = gr.inputs.Number(label="Seed", default=-1)
input_voice_fixer = gr.inputs.Checkbox(label="Voice Fixer", default=True)
input_output_path = gr.inputs.Textbox(label="Output Path", default="results/")
input_model_dir = gr.inputs.Textbox(label="Model Directory", default=MODELS_DIR)
input_high_vram = gr.inputs.Checkbox(label="Low VRAM", default=True)
input_kv_cache = gr.inputs.Checkbox(label="Key-Value Cache", default=True)
input_cond_free = gr.inputs.Checkbox(label="Conditioning Free", default=True)
input_min_chars_to_split = gr.inputs.Number(label="Min Chars to Split, must >= 50", default=150)
input_produce_debug_state = gr.inputs.Checkbox(label="Produce Debug State", default=True)

output_audio = gr.outputs.Audio(label="Generated Audio", type="numpy")

interface = gr.Interface(fn=main, inputs=[input_text, input_voice, input_preset, input_candidates,
                                          input_latent_averaging_mode, input_sampler, input_steps,
                                          input_seed, input_voice_fixer, input_output_path,
                                          input_model_dir, input_high_vram, input_kv_cache,
                                          input_cond_free, input_min_chars_to_split,
                                          input_produce_debug_state],
                         outputs=output_audio,
                         title="Tortoise TTS")

interface.launch(debug=True, share=True, inline=False)
