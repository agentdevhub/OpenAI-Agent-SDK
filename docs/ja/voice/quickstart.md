# クイックスタート

## 前提条件

まず、Agents SDK の基本的な[クイックスタート手順](../quickstart.md)に従い、仮想環境をセットアップしてください。その後、SDK のオプションである音声関連の依存関係をインストールします。

```bash
pip install 'openai-agents[voice]'
```

## コンセプト

理解すべき主なコンセプトは [`VoicePipeline`][agents.voice.pipeline.VoicePipeline] です。これは以下の 3 ステップで構成されています。

1. 音声認識モデルを実行し、音声をテキストに変換します。
2. 通常はエージェントを用いたワークフローであるコードを実行し、実行結果を生成します。
3. テキスト読み上げモデルを実行し、実行結果のテキストを再び音声に変換します。

```mermaid
graph LR
    %% Input
    A["🎤 Audio Input"]

    %% Voice Pipeline
    subgraph Voice_Pipeline [Voice Pipeline]
        direction TB
        B["Transcribe (speech-to-text)"]
        C["Your Code"]:::highlight
        D["Text-to-speech"]
        B --> C --> D
    end

    %% Output
    E["🎧 Audio Output"]

    %% Flow
    A --> Voice_Pipeline
    Voice_Pipeline --> E

    %% Custom styling
    classDef highlight fill:#ffcc66,stroke:#333,stroke-width:1px,font-weight:700;

```

## エージェント

まず、いくつかのエージェントを設定します。この SDK でエージェントを作成したことがあれば、馴染みのある内容です。ここでは、複数のエージェント、ハンドオフ、およびツールを設定します。

```python
import asyncio
import random

from agents import (
    Agent,
    function_tool,
)
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions



@function_tool
def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    print(f"[debug] get_weather called with city: {city}")
    choices = ["sunny", "cloudy", "rainy", "snowy"]
    return f"The weather in {city} is {random.choice(choices)}."


spanish_agent = Agent(
    name="Spanish",
    handoff_description="A spanish speaking agent.",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human, so be polite and concise. Speak in Spanish.",
    ),
    model="gpt-4o-mini",
)

agent = Agent(
    name="Assistant",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human, so be polite and concise. If the user speaks in Spanish, handoff to the spanish agent.",
    ),
    model="gpt-4o-mini",
    handoffs=[spanish_agent],
    tools=[get_weather],
)
```

## 音声パイプライン

ここでは、ワークフローとして [`SingleAgentVoiceWorkflow`][agents.voice.workflow.SingleAgentVoiceWorkflow] を使用し、シンプルな音声パイプラインを設定します。

```python
from agents.voice import SingleAgentVoiceWorkflow, VoicePipeline
pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(agent))
```

## パイプラインの実行

```python
import numpy as np
import sounddevice as sd
from agents.voice import AudioInput

# 簡単のため、ここでは 3 秒間の無音を作成します
# 実際にはマイクからの音声データを使用します
buffer = np.zeros(24000 * 3, dtype=np.int16)
audio_input = AudioInput(buffer=buffer)

result = await pipeline.run(audio_input)

# `sounddevice` を使ってオーディオプレイヤーを作成します
player = sd.OutputStream(samplerate=24000, channels=1, dtype=np.int16)
player.start()

# 音声ストリームをリアルタイムで再生します
async for event in result.stream():
    if event.type == "voice_stream_event_audio":
        player.write(event.data)

```

## すべてをまとめる

```python
import asyncio
import random

import numpy as np
import sounddevice as sd

from agents import (
    Agent,
    function_tool,
    set_tracing_disabled,
)
from agents.voice import (
    AudioInput,
    SingleAgentVoiceWorkflow,
    VoicePipeline,
)
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions


@function_tool
def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    print(f"[debug] get_weather called with city: {city}")
    choices = ["sunny", "cloudy", "rainy", "snowy"]
    return f"The weather in {city} is {random.choice(choices)}."


spanish_agent = Agent(
    name="Spanish",
    handoff_description="A spanish speaking agent.",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human, so be polite and concise. Speak in Spanish.",
    ),
    model="gpt-4o-mini",
)

agent = Agent(
    name="Assistant",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human, so be polite and concise. If the user speaks in Spanish, handoff to the spanish agent.",
    ),
    model="gpt-4o-mini",
    handoffs=[spanish_agent],
    tools=[get_weather],
)


async def main():
    pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(agent))
    buffer = np.zeros(24000 * 3, dtype=np.int16)
    audio_input = AudioInput(buffer=buffer)

    result = await pipeline.run(audio_input)

    # `sounddevice` を使ってオーディオプレイヤーを作成します
    player = sd.OutputStream(samplerate=24000, channels=1, dtype=np.int16)
    player.start()

    # 音声ストリームをリアルタイムで再生します
    async for event in result.stream():
        if event.type == "voice_stream_event_audio":
            player.write(event.data)


if __name__ == "__main__":
    asyncio.run(main())
```

このコード例を実行すると、エージェントがあなたに話しかけます。実際にエージェントと会話できるデモについては、[examples/voice/static](https://github.com/openai/openai-agents-python/tree/main/examples/voice/static) のコード例を参照してください。