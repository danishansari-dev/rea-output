# Ria (Reverse Engineer Anything) — Capabilities & Toolkit Reference

## Executive Summary

**Ria (Reverse Engineer Anything)** is an enterprise-grade multi-runtime reverse-engineering, decompilation, dynamic instrumentation, and software reconstruction framework. It exposes 207 specialized MCP (Model Context Protocol) tools bridging static binary analysis, runtime instrumentation, JavaScript/web bundle de-obfuscation, mobile app reverse engineering, and formal reconstruction ledgers.

This document details Ria's documented capabilities, tool taxonomy, and how Ria was used to investigate Rumik AI and guide the clean-room implementation of the **Zara** companion platform.

---

## 1. Tool Taxonomy & Core Domains

Ria's tools are structured across five primary reverse engineering domains:

```
                            ┌────────────────────────────────────┐
                            │    Ria Reverse-Engineering MCP     │
                            │           (207 Tools)              │
                            └─────────────────┬──────────────────┘
                                              │
     ┌──────────────────┬─────────────────────┼─────────────────────┬──────────────────┐
     ▼                  ▼                     ▼                     ▼                  ▼
[ Web & JS Runtime ] [ Native Binaries ]  [ Dynamic & Frida ]   [ Mobile / Android ] [ Ledger & Proofs ]
 - analyze_web_bundle - open_binary        - instrument_with_frida - inspect_apktool    - reconstruction_ledger
 - trace_web_imports  - procedure_pseudo   - start_frida_session   - decode_resources   - evaluate_coverage
 - reconcile_runtime  - batch_decompile    - observe_native_calls  - pull_adb_package   - record_unknown
 - trace_semantics    - xrefs / call_path  - rizin / gdb consoles  - search_classes     - verify_reconstruction
```

### Domain A: Web Application & JavaScript Deconstruction
Designed for single-page applications (Next.js, React, Framer), bundled frontend clients, and Electron apps.
* `analyze_web_bundle`: Captures JavaScript sources from targeted web pages and statically decomposes bundle graphs, chunk dependencies, and exposed symbols.
* `trace_web_module_imports`: Maps the dependency DAG (Directed Acyclic Graph) between code chunks, discovering shared vendor packages and internal runtime modules.
* `reconcile_javascript_runtime`: Bridges static AST code structures with runtime heap memory snapshots to reconstruct minified identifiers and obfuscated control flow.
* `trace_javascript_semantics`: Traces state machines, action dispatchers (e.g. Redux/Zustand), and data mutations inside obfuscated JavaScript.
* `compare_source_to_bundle`: Validates whether reconstructed clean-room code matches the behavior and signature shapes of target bundles.
* `inspect_web_event_listeners` & `inspect_web_network_capture`: Sniffs API contracts, WebSocket protocols, and WebRTC signaling messages directly from browser sessions.

### Domain B: Native Binary Analysis & Disassembly
Provides deep inspection of compiled binaries (PE, ELF, Mach-O, Swift, Go, Rust).
* `open_binary` & `binary_session`: Initializes native reverse engineering sessions against disassembler backends (Rizin/Ghidra/JEB).
* `procedure_pseudo_code`: Emits high-level C-like decompiled pseudo-code for identified procedures.
* `procedure_assembly`: Extracts architecture-specific disassembly (x86_64, ARM64, RISC-V) with instruction-level annotations.
* `analyze_function`: Builds comprehensive dossiers containing cyclomatic complexity, stack frame layout, local variable types, and calling conventions.
* `build_call_path`: Finds shortest direct and indirect call graphs between functions (critical for vulnerability research and control-flow tracing).
* `xrefs`: Resolves cross-references to code pointers, strings, and global tables.
* `inspect_pe_resources`, `inspect_macho`, `inspect_go_binary`, `inspect_rust_binary`: Specialized binary metadata extractors.

### Domain C: Dynamic Instrumentation & Runtime Tracing
Interactively hooks processes and monitors live execution states.
* `instrument_with_frida` & `start_frida_session`: Injects dynamic JavaScript tracing scripts into live target processes.
* `observe_native_calls`: Non-invasive tracing of API parameters, return values, and register states during function execution.
* `rizin_debug_command` & `gdb_console`: Low-level debugger interfaces for setting breakpoints, watchpoints, and inspecting process memory.
* `capture_browser_scenario` & `observe_web_execution`: Automates end-to-end user interactions while capturing DOM mutations, network traffic, and console telemetry.

### Domain D: Mobile Application Analysis (Android / Apple / Harmony)
* `inspect_apktool_client` & `decode_android_resources`: Unpacks Android APK/AAB packages, manifests (`AndroidManifest.xml`), and layouts.
* `search_android_classes` & `inspect_android_method`: Inspects DEX bytecode and reconstructed Smali/Java classes.
* `pull_adb_package` & `read_adb_logcat`: Connects to physical or emulated Android devices over ADB to capture system logs and pull installed binaries.
* `project_android_application_graph`: Constructs full architectural dependency graphs across activities, services, broadcast receivers, and native `.so` libraries.

### Domain E: Evidence Ledger & Formal Verification
Enforces scientific rigor during clean-room reimplementations.
* `build_reconstruction_obligation_ledger`: Generates a verifiable ledger of every feature, interface, and contract that must be satisfied.
* `record_unknown` & `update_unknown`: Tracks gaps in knowledge, missing parameters, and untestable assumptions.
* `verify_unknown_resolution`: Formally verifies that an unknown has been resolved with empirical proof.
* `evaluate_reconstruction_coverage`: Calculates percentage completeness of the clean-room implementation against the obligation ledger.
* `export_evidence_bundle` & `import_evidence_bundle`: Bundles all logs, network traces, decompilation snippets, and verification tests into an immutable archive.

---

## 2. Investigation Protocol Applied to Rumik AI

To investigate Rumik AI and its companion Ira without violating terms of service or security boundaries, the following non-invasive investigation protocol was executed:

1. **Static Web Bundle Analysis (`analyze_web_bundle` & scripts)**:
   - Evaluated `rumik_landing.html` and Next.js playground chunks in `playground_app/`.
   - Extracted API endpoints (`/v1/tts`, `/v1/agents`, `/v1/calls`, `/api/v1/pricing`).
   - Discovered vendor integrations: LiveKit (WebRTC audio transport), Firebase/Google Auth, Razorpay (Indian billing), PostHog (telemetry).
2. **Official Documentation Parsing (`inspect_web_page` & docs)**:
   - Analyzed OpenAPI 3.1.0 specifications for Silk API (`rumik_tts_api.md`).
   - Extracted parameter bounds, sampling arguments (`temperature: 0.6`, `top_p: 0.95`, `top_k: 50`, `repetition_penalty: 1.2`, `max_new_tokens: 2048`).
   - Retrieved prompting guides for Silk Muga 1 (`prompting-muga.md`) and Silk Mulberry 1.5 (`prompting-mulberry.md`).
3. **Public Model Hub & Weights Research**:
   - Identified open-weights release `rumik-ai/rumik-oss-1` on Hugging Face.
   - Traced architectural lineage: Tiny Aya Fire causal language model backbone + Kyutai Mimi neural audio codec.
4. **Clean-Room Obligation Formulation**:
   - Used findings to establish the exact interface and emotional behavior obligations for building Zara.
