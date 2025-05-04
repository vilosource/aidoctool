# Developer Guide: Building an Extensible LLM CLI Tool (aidoctool)

## Overview and Design Goals
aidoctool is a command-line tool that leverages Large Language Models (LLMs) (via LangChain) to perform tasks like convert and summarize documents. This guide provides a developer-oriented overview of how to implement aidoctool with a focus on clean architecture, configuration management, and extensibility. We will design the tool using SOLID principles and proven design patterns to ensure it’s easy to maintain and extend. Key features include a flexible YAML-based configuration system with multiple named LLM profiles, secure handling of API keys, and a modular CLI built with click. 

### Key design objectives:
- **Separation of Concerns (Single Responsibility):** Keep configuration handling, LLM interaction, and CLI logic in separate modules. Each component has one clear purpose, aligning with SOLID principles.
- **Open-Closed Extensibility:** Adding a new LLM provider or a new subcommand should require minimal changes to existing code. We achieve this via patterns like Factory (for LLM clients) and Strategy (for command behaviors) so the system is open for extension but closed for modification.
- **Consistent Interfaces:** Define abstract interfaces for LLM providers so that different backends (OpenAI, Anthropic, OpenRouter, etc.) can be used interchangeably (Liskov Substitution). The high-level code will interact with an LLM via a common interface, unaware of the specific provider implementation.
- **Dependency Inversion:** High-level components (like the CLI commands) depend on abstractions (LLM interface, config interface) rather than concrete implementations. Concrete providers are injected at runtime via a factory, decoupling the CLI from any one LLM API.

# Secure Configuration Management

- User settings (especially API keys) reside in a file under the user's home directory (`~/.aidoctool/config.yaml`). The tool provides CLI subcommands to manage this config file (add/edit/delete profiles, set default). Profiles encapsulate an LLM setup (provider, model, keys, etc.), and the active profile can be selected with a command-line flag (`-l`). We enforce validation on profiles (e.g. valid provider-model combinations) and handle secrets carefully (never exposing API keys in logs or error messages).

By adhering to these principles and patterns, aidoctool’s architecture will be robust, easy to navigate, and ready for future growth. In the sections below, we delve into each aspect: the YAML configuration schema, implementation patterns (Factory, Strategy, Adapter), CLI structure with click, error handling, project layout, and how to extend the tool with new providers. We’ll also walk through an example of adding and using a new profile.

## YAML Configuration System

- A core feature of aidoctool is its flexible configuration system that supports multiple profiles. A profile represents a specific LLM setup – for example, one profile might use OpenAI’s GPT-4 via the OpenAI API, while another uses an open model via OpenRouter. Users can switch between profiles without altering code, simply by selecting a profile name.

### Configuration File and Schema

- We use a YAML file at `~/.aidoctool/config.yaml` to store all settings. YAML is human-readable and allows hierarchical structuring. Below is a suggested schema for this file:

```yaml
# ~/.aidoctool/config.yaml
default_profile: default  # Name of the default profile to use if none is specified
profiles:
  default:
    provider: openrouter
    model: mixtral-8x7b
    api_key: "OPENROUTER_API_KEY_VALUE"
    # Optional additional settings can go here, e.g.:
    params:
      temperature: 0.7
      max_tokens: 1000
```

## Configuration Details

- **openai-gpt4:**
    - provider: openai
    - model: gpt-4
    - api_key: "OPENAI_API_KEY_VALUE"
    - params:
        - temperature: 0.5

- **my-anthropic:**
    - provider: anthropic
    - model: claude-v1
    - api_key: "ANTHROPIC_API_KEY_VALUE"
    - params: {}  # (Could include anthropic-specific parameters if any)

## Schema Explanation

- **default_profile:** The name of the profile to use by default when the user doesn’t explicitly specify one. This can be changed with the config default command.
- **profiles:** A mapping of profile names to their configurations.

### Profile Details
- **Profile Name:** e.g., "default", "openai-gpt4", "my-anthropic". The user can choose any name for a new profile when using config add.
- **provider:** The LLM provider or service (e.g., openai, anthropic, openrouter, etc.). This determines which API or SDK will be used.
- **model:** The model name or identifier (e.g., gpt-4, claude-v1, mixtral-8x7b). The acceptable model names depend on the provider.
- **api_key:** The API key or token for that provider (if required). This is sensitive and we must handle it safely.
- **params:** (Optional) A nested mapping for any additional parameters (like temperature, max_tokens, etc.) specific to that provider or model. This allows customization of LLM behavior per profile without hardcoding in code.

This YAML structure is easy to extend. For example, to add support for another provider like OpenAI (different models) or Anthropic, a user or the tool can simply add another profile entry. The configuration file acts as a single source of truth for all LLM settings, which the application will load at runtime.

## Loading and Saving Configuration

To work with the YAML file in code, we need functions to load it into memory (as Python dict/objects) and save it back. We can use a YAML parser like PyYAML for simplicity. Here's an example implementation of config loading/saving in Python:

```python
import os
import yaml
from pathlib import Path

CONFIG_PATH = Path.home() / ".aidoctool" / "config.yaml"
```

## Code Snippet

```python
CONFIG_PATH = Path.home() / ".aidoctool" / "config.yaml"

def load_config():
    """Load configuration from YAML file into a Python dict. Create a default structure if file missing."""
    if not CONFIG_PATH.exists():
        # If config doesn't exist, create a default structure
        return {"default_profile": None, "profiles": {}}
    with open(CONFIG_PATH, 'r') as f:
        data = yaml.safe_load(f) or {}
    # Ensure essential keys exist
    data.setdefault("profiles", {})
    data.setdefault("default_profile", None)
    return data
```  

# Code Snippet

```python
def save_config(config_data: dict):
    """Save the configuration dictionary back to the YAML file."""
    os.makedirs(CONFIG_PATH.parent, exist_ok=True)  # ensure ~/.aidoctool directory exists
    with open(CONFIG_PATH, 'w') as f:
        yaml.safe_dump(config_data, f)
```

# Implementation Notes

- If the file doesn’t exist (first run), `load_config` returns a default structure. We might later prompt the user to create a profile.
- Always ensure the directory `~/.aidoctool/` exists before writing.
- We use `yaml.safe_load/safe_dump` to parse YAML safely.
- After loading, we call `setdefault` to guarantee `profiles` and `default_profile` keys exist, which simplifies later code (avoids `KeyError`).
- The config data can be easily converted to a Pydantic model or dataclass if we want stronger typing. In a larger application, using Pydantic’s `BaseSettings` is beneficial for validation and defaults ([fullstackml.dev](https://fullstackml.dev)), but for brevity we use simple dicts here.

# Profile Management via CLI Commands

Users will manage profiles through `aidoctool config ...` subcommands rather than editing YAML by hand (though they can manually edit if they prefer). We plan the following subcommands under a main `config` command:

- `aidoctool config add <profile_name>` – Add a new profile. This command would prompt for or accept options for provider, model, and api_key (unless provided via flags). It then writes the new profile into the YAML file. If the profile name already exists, the tool should warn or ask for confirmation to overwrite.
- `aidoctool config edit <profile_name>` – Edit an existing profile. This could open the YAML in the user’s default editor (`click.edit()` can be used) or accept flags to modify specific fields (e.g., `--model new-model`). A simple approach is launching an editor with the config file, allowing the user to make changes freely.

## aidoctool config delete <profile_name>
- Remove a profile from the config. This should confirm the deletion (to avoid accidents). If the deleted profile is currently the default, consider resetting default_profile to None or to another existing profile.

## aidoctool config default <profile_name>
- Set the given profile as the new default. This updates the default_profile field in the YAML. The command should validate that the profile exists before setting it as default.

These subcommands make it easy to manage configuration without manually editing files, improving user experience. For instance, adding a new profile might look like this:

```
$ aidoctool config add my-claude --provider anthropic --model claude-v1 --api-key <YOUR_ANTHROPIC_KEY>
Profile 'my-claude' added successfully.
```

Under the hood, this would load the YAML (via load_config()), update the config_data['profiles'] with the new entry, and call save_config(). The tool should also handle edge cases: e.g., preventing a profile name that is empty or already used, ensuring required fields are provided, etc. (More on validation below.) For editing, a convenient implementation is:

```python
@click.command()
@click.argument("profile_name")
def edit(profile_name):
    config = load_config()
    if profile_name not in config["profiles"]:
        click.echo(f"Profile '{profile_name}' not found.")
        return
    # Open the config file in the editor at the relevant section (optional complexity)
    click.edit(filename=str(CONFIG_PATH))
    # After editor closes, we could reload config and inform user to ensure changes are correct.
```

For brevity, the above uses a simple approach (open entire config). A more advanced implementation could parse and only update specific fields via options.

### Safe Handling of API Keys

# Safe Handling of API Keys

API keys are sensitive credentials and must be handled with care. Do not hardcode keys in code or print them to logs. The YAML file is a convenient place to store keys for a CLI tool, but we must treat that file as sensitive.

## File Permissions

- It’s good practice to set restrictive permissions on `~/.aidoctool/config.yaml` (e.g., only readable by the user). On Unix, you might set mode 600 on the file. This prevents other local users from reading the key.

## .gitignore and Secrets

- If users are likely to put this project under version control, never commit the config file. For example, a developer might load the API key from the config file via an environment variable pointing to it, and always add that config file to `.gitignore`. The rule of thumb is to keep secrets out of source control.

## Environment Variables

- As an alternative to storing the actual API key in YAML, consider allowing the YAML to reference an environment variable. For example, `api_key: ${OPENAI_API_KEY}` could be resolved by the code at runtime. Many developers find it safest to store API keys in environment variables or a separate `.env` file. Our tool could support this by detecting placeholders or by letting an empty `api_key` field mean “use environment variable for this provider” (e.g., `OPENAI_API_KEY`).

## Masking in Output

- If the tool has a `config show` command or ever displays the config, it should mask or omit the `api_key` value (e.g., show `api_key: "********"`). This prevents accidental exposure if the user runs a verbose mode or error includes config info.

# Validation

- When adding a key via `config add`, we can validate the format (to the extent possible, e.g., OpenAI keys start with "sk-"). While we do not want to send any test requests at config time (no secret verification), basic format checks and length checks can catch obvious mistakes and prompt the user to correct them.

- By following these practices, we ensure API keys remain secure. For instance, one user approach is: use a config file for all sensitive info (including API keys) and use an environment variable to point the tool to that config file – this way the key isn’t directly in code or environment, and the config is kept out of GitHub.

- Another common practice is to rely purely on environment variables and not store keys on disk at all, but that can be less convenient for a CLI. Our approach strikes a balance by using a file (easy for the user) while urging safe handling of that file.

[community.latenode.com](https://community.latenode.com)

# CLI Architecture and Patterns

- Implementing `aidoctool` in a clean, extensible way requires thoughtful use of design patterns. We’ll discuss how the architecture applies SOLID principles and uses Factory, Strategy, and Adapter patterns to achieve modularity. We also integrate with the `click` library to handle command-line parsing elegantly.

# Applying SOLID Principles

- **Single Responsibility Principle:** Each major component of the tool has one responsibility. For example, the configuration management (loading, saving, editing YAML) is handled in one module/class, the LLM provider clients in another, and the CLI command definitions in another. This makes each piece easier to reason about and test independently.

# SOLID Principles in Software Design

### Open/Closed Principle
The system is open to extension but closed to modification. We achieve this by designing abstractions. For instance, adding a new subcommand or a new LLM provider should not require modifying the core logic of existing classes – instead, we add new classes (new Strategy or new Provider subclass) that the existing framework can integrate. This prevents regressions and keeps modifications localized.

### Liskov Substitution Principle
We define base interfaces (like an abstract LLM client). Any derived class (OpenAI, Anthropic, etc.) can be substituted wherever the base is expected. The CLI code will call methods on the base interface without caring which provider it actually is using, ensuring we can swap implementations easily.

### Interface Segregation Principle
We avoid large “god interfaces”. Instead of one gigantic class doing everything, we have focused interfaces. For example, an LLM provider interface might just have methods for generating text (and maybe for validation), and a separate interface might handle formatting or parsing if needed. This way, implementing a new provider doesn’t force implementing irrelevant methods.

### Dependency Inversion Principle
High-level modules (like the command handlers) do not depend on low-level modules directly; both depend on abstractions. Concretely, our summarize command will rely on an abstract LLM interface (e.g., call llm.generate(prompt)), not on a specific OpenAIClient or AnthropicClient. The concrete client is provided via a factory at runtime. This inversion makes it easy to plug in a different provider without changing the command logic.

By following SOLID, our codebase remains modular, testable, and extensible. Next, we detail specific design patterns used to implement these principles in practice.

## Factory Pattern for LLM Providers

# Implementing SOLID Principles in Design Patterns

By following SOLID, our codebase remains modular, testable, and extensible. Next, we detail specific design patterns used to implement these principles in practice.

## Factory Pattern for LLM Providers

We use the Factory Pattern to create LLM client instances based on the profile configuration. A factory centralizes the logic of instantiating provider-specific clients, given parameters from config. This approach decouples object instantiation from usage, improving flexibility. The CLI or business logic doesn’t need to know how to initialize an OpenAI vs. an Anthropic client; it just asks the factory for an LLM client for a given profile.

### Factory Implementation:

We define a mapping or registry of provider names to client classes (or builder functions). For example:

```python
# llm_factory.py
from aidoctool.llm.openai_client import OpenAIClient
from aidoctool.llm.anthropic_client import AnthropicClient
from aidoctool.llm.openrouter_client import OpenRouterClient
```

---

Source: unite.ai

# Registry of providers to their client classes

- `LLM_PROVIDERS`:
  ```python
  {
      "openai": OpenAIClient,
      "anthropic": AnthropicClient,
      "openrouter": OpenRouterClient
  }
  ```

## Function: `create_llm_client`

```python
def create_llm_client(profile: dict):
    """Factory method to create an LLM client instance based on profile dict."""
    provider = profile.get("provider")
    model = profile.get("model")
    api_key = profile.get("api_key")
    params = profile.get("params", {})
```

## Code Snippet
```python
if provider not in LLM_PROVIDERS:
    raise ValueError(f"Unsupported provider: {provider}")
ClientClass = LLM_PROVIDERS[provider]
# Create an instance of the appropriate client class
return ClientClass(model=model, api_key=api_key, **params)
```

## Design Pattern
Here, `OpenAIClient`, `AnthropicClient`, etc., are classes implementing a common interface (say `BaseLLMClient`). The factory function looks up the appropriate class and instantiates it. This design makes adding a new provider straightforward: implement a new client class and add one entry to the `LLM_PROVIDERS` registry. The rest of the system doesn’t need any change (Open/Closed in action).

In fact, an even more decoupled approach is to use a plugin or registry pattern: allow new provider classes to register themselves. For example, we could have each `LLMClient` subclass use a decorator or metaclass to register into `LLM_PROVIDERS` automatically. In a blog post, JO Reyes demonstrates using a decorator to register new LLM clients so that you “will not need to update the `LLMFactory` class every time you add a new LLM… just decorate the function with `register_llm_client`, and that is all you need to do for the registration” ([fullstackml.dev](https://fullstackml.dev)).

We can adopt a similar approach: define a `register_provider(name)` decorator that adds the class to the registry. New providers then simply import the decorator and apply it to their class or factory function. This eliminates even the one line change in a central registry, truly allowing plugins.

## Advantages of Using a Factory
- **Simplified Client Selection**: The CLI code can get an LLM client in one call. E.g. `llm = create_llm_client(config["profiles"][profile_name])` ([unite.ai](https://unite.ai)).
- **Decoupling & Flexibility**: We can change how clients are created (use a different SDK or adjust parameters) in one place. The rest of the code remains unaffected.
- **Extensibility**: Adding new providers is easy. A well-designed factory is extensible by nature ([medium.com](https://medium.com)).

# Markdown Formatter

- **unite.ai**
- **Extensibility:** As mentioned, adding new providers is easy. A well-designed factory is extensible by nature.
- **medium.com** 
  - One of its strengths is allowing new products (LLM clients in our case) to be integrated with minimal effort.
- **Centralized Validation:** The factory can also handle some validation. For example, if certain providers require a specific combination of parameters, the factory can check and throw a clear error if misconfigured. (Alternatively, this can be done in each client’s constructor or a separate validation function.)
- **Provider-Specific Implementation:** Each provider class (e.g., OpenAIClient) will implement a common interface. For example, we might define:

```python
# llm/base.py
from abc import ABC, abstractmethod
```

# Class Definition: BaseLLMClient

```python
class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a completion or response from the LLM given a prompt."""
        pass
```

## OpenAIClient Integration

Now, `OpenAIClient` could wrap LangChain's OpenAI integration:

### File: llm/openai_client.py

```python
from langchain.chat_models import ChatOpenAI  # example LangChain class
```

# Python Class Definitions

```python
class OpenAIClient(BaseLLMClient):
    def __init__(self, model: str, api_key: str, **params):
        # e.g., use LangChain's ChatOpenAI for chat models or OpenAI for completion models
        self.model = model
        self.api_key = api_key
        # The params dict can contain OpenAI-specific parameters like temperature, etc.
        self.client = ChatOpenAI(model_name=model, openai_api_key=api_key, **params)
    
    def generate(self, prompt: str) -> str:
        # If using chat model:
        return self.client.predict(prompt)
```

# Client Implementations

Similarly, `AnthropicClient` might use an Anthropic SDK or LangChain’s Anthropic class, and `OpenRouterClient` might call OpenRouter API endpoints. The key is they all have a `generate(prompt)` (and possibly additional methods for different kinds of prompts or chat vs. completion). This design means the `convert` or `summarize` command doesn’t care if LLM is OpenAI or something else. It will do something like:

```python
llm = create_llm_client(selected_profile_config)
result = llm.generate(user_prompt)
```

And it just works. If, say, the OpenRouter integration required an extra step (maybe selecting a model on initialization), that’s handled inside `OpenRouterClient` – transparent to the caller. By delegating the creation of LLM objects to a factory, we adhere to Dependency Inversion (high-level code depends on `BaseLLMClient`, not concrete classes) and Open/Closed (new providers via new classes, factory extension, no core changes). The factory also helps manage complexity of initialization in one spot.

# Strategy Pattern for Command Behaviors

The tool supports multiple operations (subcommands) like `convert` and `summarize`. While these share some common flow (load input, feed to LLM, output result), the details of prompting and processing differ. This is a good use case for the Strategy Pattern, which lets us define a family of algorithms and choose one at runtime. 

Source: [unite.ai](unite.ai)

# Markdown Formatter

- **Website**: [unite.ai](https://unite.ai)

The logic for each subcommand can be encapsulated in its own class or function, following a common interface. Using strategy classes for each command enables the CLI code to be generalized. For instance, a generic command handler could select the appropriate strategy based on the invoked command. This separation keeps the code for each operation distinct and simplifies adding new operations (simply include a new strategy class + CLI hook).

## Implementation Approach

Define an abstract base class for the "Task Strategy":

```python
# commands/strategies.py
from abc import ABC, abstractmethod
```

## Task Strategy Interface

```python
class TaskStrategy(ABC):
    @abstractmethod
    def run(self, llm_client, input_path: str, output_path: str = None):
        """Execute the task using the given llm_client on input data, optionally writing to output_path."""
        pass
```

To implement concrete strategies for each subcommand, follow the example below:

### Summarize Strategy

```python
class SummarizeStrategy(TaskStrategy):
    def run(self, llm_client, input_path: str, output_path: str = None):
        # Load the input text (e.g., from a file path)
        with open(input_path, 'r') as f:
            content = f.read()
        
        # Formulate a prompt for summarization
        prompt = f"Summarize the following document:\n\n{content}\n\n## End of document.\nProvide a concise summary."
        
        summary = llm_client.generate(prompt)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(summary)
        else:
            print(summary)
        
        return summary
```

## Class Definition: ConvertStrategy

```python
class ConvertStrategy(TaskStrategy):
    def __init__(self, target_format: str):
        self.target_format = target_format  # e.g., "markdown", "pdf", etc.
    def run(self, llm_client, input_path: str, output_path: str = None):
        with open(input_path, 'r') as f:
            content = f.read()
        prompt = f"Convert the following document to {self.target_format} format:\n\n{content}"
        converted = llm_client.generate(prompt)
        if output_path:
            with open(output_path, 'w') as f:
                f.write(converted)
        else:
            print(converted)
        return converted
```

In this design, each strategy knows how to construct the LLM prompt and handle the result for that specific task. The SummarizeStrategy might add specific instructions to ensure a concise summary, whereas ConvertStrategy might instruct the model to output a certain format. If in the future we add a translate command, we can create a TranslateStrategy without touching the existing ones. The CLI command functions then simply select the appropriate strategy. For example, in the summarize command function:

### Summarize Command Function
```python
def summarize_command(input_path, output_path=None, profile_name=None):
    config = load_config()
    profile = profile_name or config.get("default_profile")
    profile_data = config["profiles"].get(profile)
    llm = create_llm_client(profile_data)
    strategy = SummarizeStrategy()
    strategy.run(llm, input_path, output_path)
```

And for convert, perhaps we accept an option for `--to` format:

### Convert Command Function
```python
def convert_command(input_path, target_format, output_path=None, profile_name=None):
    # ... similar loading profile ...
    llm = create_llm_client(profile_data)
    strategy = ConvertStrategy(target_format)
    strategy.run(llm, input_path, output_path)
```

By using the strategy pattern, we encapsulate each algorithm (summarizing vs converting) separately

Source: unite.ai

## Code Execution Strategy

- `strategy.run(llm, input_path, output_path)`
- By using the strategy pattern, we encapsulate each algorithm (summarizing vs converting) separately
- This makes the code cleaner and each strategy class adheres to single-responsibility (formatting and handling that specific task).
- We can even expose a hook for external plugins: e.g., allow registering new strategies if someone wants to extend aidoctool with a completely new subcommand (though integrating with click would also be needed).
- It’s worth noting that for only two commands, one might think strategy classes are overkill; however, as the tool grows (imagine adding translate, analyze, etc.), this pattern pays off by keeping the logic modular. It also makes unit testing easier (you can test SummarizeStrategy independently by mocking an llm_client).

## Adapter Pattern for LangChain Integration

- aidoctool uses LangChain under the hood to leverage LLMs.
- LangChain provides its own interfaces and classes for models, chains, and prompts.
- To keep our tool independent of LangChain’s specifics and to allow flexibility to switch to another library or direct API in the future, we use an Adapter Pattern.
- The Adapter Pattern is a structural design pattern that “allows objects with incompatible interfaces to work together”, essentially acting as a bridge between our code and the third-party library.
- Why an adapter? LangChain’s model classes (for example, ChatOpenAI or Anthropic) have their own methods and may expect input in certain formats (like a list of HumanMessage/SystemMessage for chat models).
- In our tool, we want a simple `llm_client.generate(prompt: str) -> str` interface.
- An adapter will convert our simple interface calls into the LangChain calls:
  - It hides the complexity of LangChain’s Message objects or chain execution from the rest of our code.

## Adapter Pattern in Software Development

- It hides the complexity of LangChain’s Message objects or chain execution from the rest of our code.
- It prevents our code from being tightly coupled to LangChain. If later we decide to call the OpenAI API directly (bypassing LangChain) or switch to a different framework, we can do so by changing the adapter implementation, without changing the high-level logic. This follows the principle of integrating third-party libraries via adapters so that their interface differences don’t leak into your core code.

Source: [medium.com](https://medium.com)

### Adapter in Practice

In fact, our OpenAIClient, AnthropicClient classes in the Factory example above are acting as adapters. They adapt LangChain’s interface to our BaseLLMClient interface. For example, `OpenAIClient.generate()` might internally do:

```python
output = self.langchain_llm.predict(prompt)  # LangChain call
return output
```

Here, `langchain_llm` could be an instance of `langchain.chat_models.ChatOpenAI` or similar. If LangChain’s API changes or if we want to use a raw HTTP request to OpenAI, we just modify `OpenAIClient` – the rest of `aidoctool` doesn’t need to know. The adapter thus “wraps the old interface and provides the expected one”.

Source: [medium.com](https://medium.com)

Another example: Suppose LangChain requires messages like:

```python
messages = [SystemMessage(content="You are a converter."), HumanMessage(content=content)]
response = self.chain.run(messages)
```

# Code Implementation Details

```python
messages = [SystemMessage(content="You are a converter."), HumanMessage(content=content)]
response = self.chain.run(messages)
```

Our adapter can hide this by providing a `convert_document(content)` method that does the above internally. The CLI code would simply call `adapter.convert_document(text)` as if it were a native method.

## Multiple Adapters

You might have different adapter logic for different modes. E.g., one adapter for chat-based models (where you might pass system and user messages), another for completion-based models. This can be handled via different client classes or within one class branching on model type.

## LangChain vs Direct API

By keeping LangChain usage confined behind adapter classes, we also allow advanced users to plug in direct API calls if needed. For instance, if `OpenRouterClient` isn’t supported by LangChain, we could implement it with direct HTTP calls to OpenRouter’s API. To the outside, it still presents `generate(prompt)` – an adapter/wrapper around the HTTP calls. This way, whether a provider is accessed via LangChain or via custom code, the rest of the system is none the wiser (polymorphism at work).

In summary, the Adapter pattern ensures interface compatibility between our `aidoctool` internals and external libraries. It makes future integrations smoother: “when using a third-party library that doesn’t match the interface of your application,” an adapter is the go-to solution.

[Read more on Medium](https://medium.com)

## Implementing the CLI with Click

We use the Click library to build the command-line interface. Click supports grouping commands, parsing options, and providing helpful output. Our CLI will be organized into a main command group (`aidoctool`) with subcommands for each operation (e.g., convert, summarize) and a subgroup for config management commands.

### Why Click?

Click makes it easy to define commands with decorators and supports nested subcommands (via `click.Group`). Grouping commands improves organization, keeps code modular, and scales as the application grows.

# mteke.com

## CLI Command Structure

We define a main entry point and group using `@click.group()` and then attach subcommands. For example:

```python
import click
from aidoctool.config import load_config, save_config
from aidoctool.commands import summarize_command, convert_command
```

## Code Snippet

```python
@click.group()
@click.option('-l', '--profile', 'profile_name', default=None,
              help="Name of the profile to use (overrides default profile)")
@click.pass_context
def cli(ctx, profile_name):
    """aidoctool - CLI for LLM document conversion and summarization."""
    # Load config once and pass it to subcommands via context
    config = load_config()
    # Determine active profile: CLI flag overrides default
    active_profile = profile_name or config.get("default_profile")
    ctx.obj = {
        "config": config,
        "profile": active_profile
    }
```

In this snippet:
We allow a global option -l/--profile on the root command to select a profile at runtime. The ctx.obj (a Click context object) is used to store the loaded config and selected profile, so that subcommands can access it [github.com](github.com). Using ctx.obj is a common pattern to carry objects (like config or database connections) through Click’s invocation flow.

If -l is not provided, we use the default_profile from the config. If even that is not set (e.g., no default and user didn’t specify), active_profile might be None. We should handle that scenario (e.g., prompt the user to run config add).

## Subcommands

```python
@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', 'output_file', type=click.Path(writable=True),
              help="Optional path to save the output")
@click.pass_context
def summarize(ctx, input_file, output_file):
    """Summarize the given input document."""
    profile = ctx.obj["profile"]
    config = ctx.obj["config"]
    profile_data = config["profiles"].get(profile)
    if not profile_data:
        raise click.UsageError(f"Profile '{profile}' not found in config.")
    # Create LLM client and run summarization
    llm = create_llm_client(profile_data)
    from aidoctool.commands import SummarizeStrategy  # or summarize_command function
```

# Create LLM client and run summarization

```python
llm = create_llm_client(profile_data)
from aidoctool.commands import SummarizeStrategy  # or summarize_command function
result = SummarizeStrategy().run(llm, input_file, output_file)
# If needed, indicate where summary was saved
if output_file:
    click.echo(f"Summary saved to {output_file}")
```

# Convert

```python
@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--to', 'target_format', required=True, help="Target format to convert to (e.g., markdown)")
@click.option('-o', '--output', 'output_file', type=click.Path(writable=True))
@click.pass_context
def convert(ctx, input_file, target_format, output_file):
    """Convert the document to the specified format using an LLM."""
    profile = ctx.obj["profile"]
    config = ctx.obj["config"]
    profile_data = config["profiles"].get(profile)
    if not profile_data:
        raise click.UsageError(f"Profile '{profile}' not found. Please check your config.")
    llm = create_llm_client(profile_data)
    result = ConvertStrategy(target_format).run(llm, input_file, output_file)
    if output_file:
        click.echo(f"Converted output saved to {output_file}")
```

# Config

```python
@cli.group()
def config():
    """Manage aidoctool configuration profiles."""
    pass
```

## Python Script for Adding Configuration

```python
@config.command('add')
@click.argument('profile_name')
@click.option('--provider', prompt=True, help="Provider name (e.g., openai, anthropic)")
@click.option('--model', prompt=True, help="Model name (e.g., gpt-4, claude-v1)")
@click.option('--api-key', prompt=True, hide_input=True, help="API key for the provider")
def config_add(profile_name, provider, model, api_key):
    cfg = load_config()
    profiles = cfg.setdefault("profiles", {})
    if profile_name in profiles:
        raise click.ClickException(f"Profile '{profile_name}' already exists.")
    profiles[profile_name] = {"provider": provider, "model": model, "api_key": api_key, "params": {}}
    if not cfg.get("default_profile"):
        cfg["default_profile"] = profile_name  # Set default if not set
    save_config(cfg)
    click.echo(f"Profile '{profile_name}' added.")
```

This Python script defines a function `config_add` that adds a new profile with specified provider, model, and API key to the configuration.

# Implementation Details

- Similarly, config edit, delete, default can be implemented...

## Configuration Subgroup

In the above:
- We make config a subgroup of cli. So usage will be `aidoctool config add ....`
- The `--provider`, `--model`, and `--api-key` options for config add are prompted if not provided (using Click’s `prompt=True`, and `hide_input=True` for API key to not echo it).
- We update the YAML through our config functions. 
- We also demonstrate setting the first added profile as default if none exists, to avoid a situation where no default is set.

## User-Friendly CLI

Using Click in this way ensures the CLI is user-friendly. The grouping keeps it organized: convert and summarize as primary commands, and config commands in their own namespace. This structure is clear to users (they can do `aidoctool --help` and see subcommands and usage). 

A note on global options vs per-command options:
- We chose to implement profile selection `-l/--profile` as a global option on the group (using `@click.group` with `@click.option`). 
- This means the user can put `-l profileName` after the main command too, e.g. `aidoctool -l openai-gpt4 summarize file.txt`. 

Click’s context ensures `ctx.obj` persists and is available in subcommands.
- An alternative approach is to have each command accept a `--profile` option. That is a bit more repetitive, but it localizes the option. Either approach is valid. 
- The global option approach requires careful handling to pass it down, which we’ve done with pass_context and `ctx.obj`.

## Error Handling and Validation in CLI

We want the tool to be robust and give informative errors without Python stack traces in user’s face for expected errors (like a missing profile). Here’s our strategy:
- Profile Existence: As shown, when using a profile, we check if `profile_data` exists. If not, we raise a `click.UsageError` or `ClickException` with a clear message (Click will catch this and print it as an error message). This guides the user to fix their config or specify the correct profile.

Source: [github.com](github.com)

# Input/Output Paths

- Using Click’s `type=click.Path(exists=True)` for input file automatically validates that the input path exists.
- For output, `writable=True` ensures we can open it.
- We should also handle exceptions during file reading/writing (e.g., permission issues) and report them.

# API Errors

- When the LLM client calls the provider API (via LangChain or direct), things can go wrong (network issues, invalid API key, model not available, etc.).
- The `generate()` method in our client classes should catch known exceptions (e.g., `openai.error.OpenAIError`) and either wrap them in a custom exception or return a user-friendly error.
- We might propagate an error up to the CLI level and print an error. For example:

```python
try:
    summary = llm_client.generate(prompt)
except Exception as e:
    # You might catch specific exceptions for known issues
    raise click.ClickException(f"LLM generation failed: {str(e)}")
```

- Using `ClickException` will ensure the message is printed without a traceback.

# Validating Provider/Model Combos

- Because we want to catch configuration mistakes early, we can implement validation rules:
  - Maintain a dictionary of supported models for each provider (if known). For instance, `{"openai": ["gpt-3.5-turbo", "gpt-4", ...], "anthropic": ["claude-v1", ...], "openrouter": ["mixtral-8x7b", ...]}`.
  - On config add or config edit, check if the model is in the allowed list for that provider. If not, warn the user or prevent it. This list can be in code or even part of the config schema.
  - The `create_llm_client` factory could also do a sanity check: e.g., if provider is `openai` but model name looks like an Anthropic model, log or throw an error. However, since models update often, this could become outdated. It might be better to do a basic check and otherwise rely on the provider’s API to error out (for example, OpenAI API will error if an unknown model is requested).
- If a profile has missing fields (no provider or model), we should raise an error when trying to use it.

## If a profile has missing fields (no provider or model), we should raise an error when trying to use it

- Graceful Degradation: For network issues or provider downtime, a possible advanced feature is a retry mechanism or even a fallback provider. For instance, the factory or client could implement retries on timeout ([medium.com](https://medium.com)), or if a provider is unreachable, fall back to another provider (perhaps user-configured) ([medium.com](https://medium.com)). This is optional, but worth noting as a design consideration for reliability.

- Click Exception Handling: Click automatically handles ClickException and UsageError by printing the message and aborting with a non-zero exit code. Unhandled exceptions would show a stack trace; to avoid that for foreseeable errors, catch them and use ClickException. For truly unexpected bugs, we might let them bubble up so the developer can see the stack trace.

- By validating input early and catching errors around external calls, aidoctool can provide a smooth user experience. An example of a friendly error might be:
  ```
  $ aidoctool summarize report.txt
  Error: Profile 'default' not found in config. Please add it or specify a profile with -l.
  ```
  This is much better than a KeyError traceback. In tests, we should simulate various error conditions to ensure the messages make sense.

## Project Structure and Organization

Organizing the project into modules helps maintain the code. Here’s a recommended directory structure for aidoctool:

```
aidoctool/
├── __init__.py
├── cli.py              # Entry point definitions for the CLI commands using click
├── config.py           # Functions and possibly classes for config handling (load/save, maybe a Config class)
├── commands/
│   ├── __init__.py
│   ├── strategies.py   # Strategy classes for different subcommands (SummarizeStrategy, ConvertStrategy, etc.)
│   └── # (optional) alternatively, separate files per command:
│   ├── summarize.py    # could contain SummarizeStrategy or related logic
│   └── convert.py
├── llm/
│   ├── __init__.py
```

# Project Structure

```
project/
│
├── cli.py              # Defines the click groups and commands.
│
├── config.py           # Contains load_config, save_config, and ConfigManager class.
│
├── commands/           # Contains the implementations of the functionalities.
│   ├── summarize.py    # Could contain SummarizeStrategy or related logic.
│   └── convert.py
│
├── llm/
│   ├── __init__.py
│   ├── base.py         # BaseLLMClient class (abstract interface)
│   ├── openai_client.py       # OpenAIClient implementation
│   ├── anthropic_client.py   # AnthropicClient implementation
│   ├── openrouter_client.py  # OpenRouterClient implementation
│   └── # other providers as needed
│
├── utils/              # For utility functions like formatting outputs or reading files.
│   └── __init__.py
│
└── main.py             # If using a separate script to invoke the CLI.
```

## Explanation

- **cli.py:** Defines the click groups and commands. Imports from other modules like config.py, commands/strategies.py, etc.
  
- **config.py:** Contains load_config, save_config, and possibly a ConfigManager class for configuration file interactions.
  
- **commands/:** Contains the implementations of the functionalities. Strategies should be free of click and focus on processing for independent testing. For example, `SummarizeStrategy().run(llm, "input.txt")` can be tested with a dummy llm.

## Project Structure

- **llm/**: Contains all LLM provider related code. Each provider’s integration is encapsulated in its class. The `base.py` defines the interface and perhaps some common functionality (like a base class that stores model name, etc.). If using LangChain, these classes act as adapters to LangChain as discussed. If not using LangChain for some provider, the class will handle the API calls directly.
- **utils/**: Optional, for generic helper functions (e.g., if we have a function to pretty-print output, or to mask API keys when displaying config, etc.).
- **main.py**: This could be a simple wrapper that calls `cli()` from `cli.py` if we prefer to have an explicit entry. Alternatively, using a `console_scripts` entry point in `setup.py/pyproject.toml` can directly point to `aidoctool.cli:cli` function to create the command-line executable.

### Additional Files

- **README.md**: Document how to install and use the tool (for users).
- **requirements.txt** or **pyproject.toml**: include dependencies like `click`, `pyyaml`, `langchain`, etc.
- **Tests**: A `tests` directory for unit tests (testing config load/save, strategy logic, maybe using `pytest` and `monkeypatch` to simulate API calls).

This structure respects separation: configuration logic doesn’t import CLI, CLI doesn’t implement business logic, etc. It also mirrors the responsibilities (which aligns with single-responsibility principle).

## Extending with New LLM Providers

One of our goals is to make it easy to add support for new LLM providers (e.g., OpenAI, Anthropic, Cohere, HuggingFace Hub, etc.). Thanks to the abstractions we put in place, adding a new provider typically involves:

Create a new client class in `aidoctool/llm/`. For example, if adding HuggingFace Hub:

```python
# llm/huggingface_client.py
class HuggingFaceClient(BaseLLMClient):
    def __init__(self, model: str, api_key: str, **params):
        # Use HuggingFace Inference API or SDK initialization
        self.model = model
        self.api_key = api_key
        # maybe initialize a HuggingFace pipeline or client here
```

# Use HuggingFace Inference API or SDK Initialization

```python
self.model = model
self.api_key = api_key
# maybe initialize a HuggingFace pipeline or client here
```

The `generate` method should be implemented to call the HuggingFace API and return the result.

Ensure this class implements the required interface (`generate`). It can accept and store any necessary parameters in `__init__`. Use the API key securely (likely pass it to the HuggingFace SDK or use an environment var if needed).

## Registering the Provider

Register the provider in the factory. If using a simple dictionary approach, add:

```python
from aidoctool.llm.huggingface_client import HuggingFaceClient
LLM_PROVIDERS["huggingface"] = HuggingFaceClient
```

If using a plugin mechanism (e.g., entry points or a decorator), then ensure the class is decorated or the plugin is installed. For instance, if we had an entry point group like `aidoctool.providers`, the new provider package could add an entry in its setup to advertise the new class. Our `aidoctool` could then dynamically load these entry points at startup to populate the registry.

## Updating Configuration

Update configuration if needed: The YAML schema is flexible enough; the user can now add a profile with `provider: huggingface`. If certain providers need extra config (say a base URL or organization ID), we can accommodate that by allowing extra fields in the profile’s params. In our example, anything under params will be passed to the client class. For HuggingFace, maybe an `api_url` or something could be passed that way.

## Validation

Validation: Optionally update any validation logic to include the new provider’s models. Or have the new client class perform validation. For example, `HuggingFaceClient.__init__` might check that the model string is not empty or matches a pattern.

## Testing

Testing: Test the new integration by adding a profile and running a command.

## Testing New Integration

- Test the new integration by following these steps:
  1. Add a profile.
  2. Run a command.

Because our CLI and command logic are decoupled from specific providers, you typically do not need to modify the core logic at all – just plug in the new class and config. This reflects the Factory pattern’s extensibility: "add new providers or customize existing ones" easily ([source](https://medium.com)).

For a plugin mechanism, we could implement a simple registry in `llm/base.py`:

```python
PROVIDER_REGISTRY = {}
```

## Code Snippet

```python
def register_provider(name):
    def decorator(cls):
        PROVIDER_REGISTRY[name] = cls
        return cls
    return decorator
```

## Using `register_provider`

```python
@register_provider("huggingface")
class HuggingFaceClient(BaseLLMClient):
    ...
```

## Modifying `create_llm_client`

Modify `create_llm_client` to use `PROVIDER_REGISTRY`. This way, even an external module can import `register_provider` and use it, and as long as that module is imported, the provider is registered. We could auto-import providers package in `cli.py` to ensure all built-ins register on startup. Another advanced option is using `importlib.metadata.entry_points()`. We could define that external packages can advertise entry points like:

```ini
[options.entry_points]
aidoctool.providers =
    huggingface = myplugin.hf:PluginHuggingFaceClient
```

Our factory loader would then iterate through `entry_points(group="aidoctool.providers")` and register each. This allows truly plug-and-play extensibility (no need to even modify the main codebase to add a new provider, just install a plugin package).

Example – adding Anthropic support: Suppose originally we only had OpenAI and OpenRouter. Now we want Anthropic:

1. Install anthropic SDK or use LangChain’s Anthropic integration.
2. Create `AnthropicClient` class in our code. Perhaps use LangChain’s `ChatAnthropic`.
3. Register it in factory (say provider name "anthropic").
4. Instruct user to add a profile:

```yaml
profiles:
    my-anthropic:
        provider: anthropic
        model: claude-v1
        api_key: "ANTHROPIC_API_KEY"
```

Now the user can run with `-l my-anthropic` and our system will route calls to the `AnthropicClient`.

This modular design, leveraging a registry/factory, exemplifies the Open-Closed principle: new functionality via new classes, not by changing the core logic. As one article noted about a unified LLM factory, “when a new model comes around, all we have to do is register the new model” ([fullstackml.dev](https://fullstackml.dev)) – our approach achieves exactly that.

## Example Workflow: Adding and Using a New Profile

# fullstackml.dev

- our approach achieves exactly that.

## Example Workflow: Adding and Using a New Profile

Let's walk through a concrete example to solidify how everything works together. Imagine a user just installed aidoctool and wants to use it with their OpenAI API key and also try out OpenRouter for a different model.

### Initial Setup

User runs aidoctool for the first time. Behind the scenes, `load_config()` doesn’t find a config file, so it creates an empty config structure. The user needs to add a profile.

### Adding a Profile (OpenAI)

The user executes:

```bash
$ aidoctool config add openai-gpt4 --provider openai --model gpt-4 --api-key sk-...
```

The CLI `config add` command calls `config_add` function. This loads the current config (empty), then adds:

```yaml
profiles:
  openai-gpt4:
    provider: openai
    model: gpt-4
    api_key: "sk-..."   # user's OpenAI key
    params: {}
default_profile: openai-gpt4   # set as default since none was set
```

The tool saves the YAML and prints confirmation. The config file now exists with the OpenAI profile set as default.

### Using the Profile

Now the user runs a command:

```bash
$ aidoctool summarize -o summary.txt report.pdf
```

(Assume the tool can handle PDF by perhaps converting to text internally, or perhaps it expects text – for this example, assume report.pdf is already text or the user gave a text file.)

Click parses this: summarize command, `-o summary.txt` for output, `report.pdf` as input file. No `-l` provided, so `ctx.obj["profile"]` will be `openai-gpt4` (the default).

Inside `summarize_command` (or our click handler), we fetch `profile_data` for `openai-gpt4` from config. It's found (provider openai, model gpt-4, api_key provided).

We call `create_llm_client(profile_data)`. The factory sees provider == "openai" and instantiates `OpenAIClient(model="gpt-4", api_key="sk-...")`. This in turn sets up a LangChain ChatOpenAI with model gpt-4 and the API key.

## Summarization Process

- We then call our SummarizeStrategy: it reads `report.pdf` (we might integrate a PDF to text step if needed, but let's assume it’s plain text for simplicity) and creates a prompt for summarization. It calls `llm_client.generate(prompt)`.
- The `OpenAIClient.generate` method sends the prompt to the OpenAI API (via LangChain). Suppose the API responds with a summary text.
- The strategy receives the summary, and since `-o summary.txt` was given, it writes the summary to that file. The CLI then prints a message "Summary saved to `summary.txt`".
- The user opens `summary.txt` and sees the generated summary.

## Adding Another Profile (OpenRouter)

- Now the user wants to try a model via OpenRouter (an aggregator service). They run:
```
$ aidoctool config add my-mistral --provider openrouter --model mixtral-8x7b --api-key <OPENROUTER_KEY>
```
- This adds a new profile `my-mistral` to the YAML. It does not change the `default_profile` (still `openai-gpt4`) unless the user explicitly changes `default`.
- Now profiles have two entries. The user can list or show them (if we implement `config list` or similar).

## Using the New Profile

- The user runs the convert command with the new profile:
```
$ aidoctool convert --to markdown -l my-mistral design_doc.txt -o design_doc.md
```
- Here `-l my-mistral` explicitly selects the OpenRouter profile for this run.
- The CLI context sets `ctx.obj["profile"] = "my-mistral"`.
- In the convert command, we load that profile. Factory creates an OpenRouterClient (with model `mixtral-8x7b` and the provided key). This client might call OpenRouter’s API endpoint with the given model to get a completion.
- The `ConvertStrategy("markdown")` is used; it sends a prompt like “Convert the following document to markdown…” along with the content of `design_doc.txt`.
- The OpenRouter model returns the converted markdown text (in theory).
- The tool writes it to `design_doc.md`.
- User gets the message and opens the markdown file to verify the conversion.

## Error Handling Example

- Suppose the user made a typo in the provider name:

# Design Documentation

## Writing to File

The tool writes it to `design_doc.md`.

## Verification Process

User gets the message and opens the markdown file to verify the conversion.

## Error Handling Example

Suppose the user made a typo in provider name:

```bash
$ aidoctool config add testprofile --provider openaii --model gpt-3 --api-key abc...
```

The `config_add` function sees provider "openaii" which is not recognized. We could catch this by checking against allowed providers list (`openai`, `anthropic`, `openrouter`, etc.). If not recognized, we output an error: 

```
Error: Unsupported provider 'openaii'. Valid providers are: openai, anthropic, openrouter.
```

The profile would not be added. The user can then correct the command.

## Advanced Use

If the user wants to quickly switch default:

```bash
$ aidoctool config default my-mistral
```

This sets `default_profile: my-mistral` in the YAML. Now running `aidoctool summarize ...` without `-l` would use `my-mistral` by default.

## Key Architectural Pieces

Throughout this workflow, the key architectural pieces are in play:

- YAML config allows multiple profiles and persistent settings.
- Factory creates appropriate LLM adapter based on profile.
- Strategy handles task-specific prompting.
- Adapter (client class) interfaces with LangChain or API.
- The CLI (Click) glues everything, parsing arguments and invoking the right components, while providing helpful messages and handling errors (like unknown profile or file issues).

The user can continue to extend the config (add profiles for other models/providers) and the tool remains stable. Developers maintaining the tool can add features like new subcommands (just add a new Strategy and CLI command) or new providers (add class + registry entry) without touching unrelated parts, reducing risk of bugs. This fulfills our goal of an extensible, developer-friendly CLI for LLM operations.

## Conclusion

# Conclusion

In this guide, we covered how to build `aidoctool` – a command-line tool powered by LLMs – with a focus on solid architecture and extensibility. We designed a robust configuration system using YAML profiles, enabling easy switching between multiple LLM setups. We leveraged SOLID principles to separate concerns and keep the design maintainable, and we applied design patterns to our advantage:

- A Factory pattern centralizes LLM client creation and makes adding new providers straightforward ([source](https://medium.com))
- Strategy pattern cleanly encapsulates different command behaviors (summarize, convert, etc.) and allows extending functionality without breaking existing code ([source](https://unite.ai))
- Adapter pattern decouples our code from LangChain’s interfaces, acting as a bridge so we can integrate or swap out third-party components easily ([source](https://medium.com))

We also integrated with the `click` library to build a user-friendly CLI, organizing commands into groups for clarity and using context to manage state across subcommands. We emphasized thorough error handling and validation: from configuration validation (ensuring profiles make sense) to graceful error messages for runtime issues, and outlined strategies for handling API keys securely to protect user secrets ([source](https://community.latenode.com)).

By following this guide, developers can implement `aidoctool` or a similar CLI tool confidently. The resulting application will be well-structured: easy to extend (supporting new LLMs or commands), easy to configure (with profile management commands and a clear YAML schema), and easy to use (thanks to a consistent CLI interface and helpful feedback). With the rapid advancements in the LLM space, such an extensible design ensures your tool can evolve by simply plugging in new components rather than refactoring core logic – a critical advantage in a fast-moving field.

# Citations

- Favicon
- Design Patterns in Python for AI and LLM Engineers: A Practical Guide - Unite.AI

## Articles and Guides

- [Design Patterns in Python for AI and LLM Engineers: A Practical Guide](https://www.unite.ai/design-patterns-in-python-for-ai-and-llm-engineers-a-practical-guide/) - Unite.AI
- [#7 - Streamline Your AI Workflow: A Factory Class for LLMs and Embedding Models](https://fullstackml.dev/p/7-streamline-your-ai-workflow-a-factory) - Favicon
- [What's the smartest method for storing your OpenAI API key? - API - Latenode Official Community](https://community.latenode.com/t/whats-the-smartest-method-for-storing-your-openai-api-key/6974) - Favicon
- [Streamlining Your AI Development with a Unified LLM Factory in Python](https://medium.com/@alwinraju/streamlining-your-ai-development-with-a-unified-llm-factory-in-python-69ba97cd2bc2) - by Alwin Raju - Favicon
- [Understanding the Adapter Pattern in Python](https://medium.com/@goldengrisha/understanding-the-adapter-pattern-in-python-328c9d7c43d0) - by Gregory Kovalchuk - Favicon

## Additional Resources

- [Creating CLI Tool with Click in Python Part-2](https://www.mteke.com/creating-cli-tool-with-click-in-python-part-2/) - Favicon
- [GitHub - click-contrib/click-repl: Subcommand REPL for click apps](#)

# Links

- [Creating CLI Tool with Click in Python - Part 2](https://www.mteke.com/creating-cli-tool-with-click-in-python-part-2/)
- [GitHub - click-contrib/click-repl: Subcommand REPL for click apps](https://github.com/click-contrib/click-repl)
- [Streamlining Your AI Development with a Unified LLM Factory in Python | by Alwin Raju | Medium](https://medium.com/@alwinraju/streamlining-your-ai-development-with-a-unified-llm-factory-in-python-69ba97cd2bc2)
- [Streamline Your AI Workflow: A Factory Class for LLMs and Embedding Models](https://fullstackml.dev/p/7-streamline-your-ai-workflow-a-factory)