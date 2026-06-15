"""Package, provenance, policy, and signing command registration."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer


def register_package_commands(app: typer.Typer) -> None:
    """Register package, provenance, policy, and signing commands."""

    @app.command()
    def bundle_verify(
        bundle_path: Annotated[Path, typer.Argument(help="Path to context bundle.")],
    ) -> None:
        """Verify a context bundle's provenance and content hash (Phase 9)."""
        from sayane.core.import_bundle import parse_bundle
        from sayane.core.bundle_provenance import verify_bundle

        parsed = parse_bundle(bundle_path)
        if parsed is None:
            raise typer.BadParameter(f"Could not parse bundle: {bundle_path}")

        result = verify_bundle(parsed)
        typer.echo("Bundle verification:")
        typer.echo(f"  Status: {result.status}")
        typer.echo(f"  Bundle ID: {result.bundle_id or 'N/A'}")
        if result.hash_value:
            typer.echo(f"  Hash: sha256:{result.hash_value}")
        typer.echo(f"  Signature: {result.signature_status}")
        if result.details:
            typer.echo(f"  Details: {result.details}")

    @app.command()
    def transfer_report(
        output: Annotated[Path, typer.Option("--output", "-o", help="Output file path.")] = Path("docs/transfer-tests/transfer-regression-report.md"),
        format: Annotated[str, typer.Option("--format", help="Output format: markdown | json | html")] = "markdown",
        fixtures_dir: Annotated[Path, typer.Option("--fixtures", help="Transfer fixtures directory.")] = Path("docs/transfer-tests"),
        audit_path: Annotated[Path | None, typer.Option("--audit", help="Audit store path.")] = None,
        fail_on_warnings: Annotated[bool, typer.Option("--fail-on-warnings")] = False,
    ) -> None:
        """Generate a cross-LLM transfer regression dashboard report (Phase 10/F-5)."""
        from sayane.core.audit_trail import AuditStore
        from sayane.core.transfer_report import generate_transfer_report, render_markdown_report

        audit_dir = audit_path.parent if audit_path else Path.home() / ".sayane" / "audit"
        audit_store = AuditStore(audit_dir) if audit_path else AuditStore(audit_dir)

        report = generate_transfer_report(
            transfer_dir=fixtures_dir,
            audit_store=audit_store,
            profile_path=Path("examples/profiles/minimal.yaml"),
        )

        if format == "json":
            import json as _json
            content = _json.dumps(report, ensure_ascii=False, indent=2)
        elif format == "html":
            from sayane.core.transfer_report_html import render_html_report
            content = render_html_report(report)
        else:
            content = render_markdown_report(report)

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        typer.echo(f"Report written: {output}")

        status = report["status"]
        if status == "FAIL":
            raise typer.Exit(1)
        if fail_on_warnings and status == "PASS_WITH_WARNINGS":
            raise typer.Exit(1)

    @app.command()
    def policy(
        action: Annotated[str, typer.Argument(help="list | show | validate")],
        profile_name: Annotated[str | None, typer.Argument()] = None,
        policy_file: Annotated[Path | None, typer.Option("--file", help="Policy file path.")] = None,
        strict: Annotated[bool, typer.Option("--strict", help="Strict validation.")] = False,
    ) -> None:
        """List, show, or validate import policy profiles (Phase 11/15)."""
        del strict
        import json as _json
        from sayane.core.import_policy import get_policy, list_policies

        if action == "list":
            names = list_policies()
            typer.echo(f"Available policies: {', '.join(names)}")
            return

        if action == "validate":
            if not policy_file:
                raise typer.BadParameter("--file required for validate")
            from sayane.core.policy_file import load_and_validate, resolve_effective_policy

            policy_data, errors = load_and_validate(policy_file)
            if errors:
                typer.echo("Invalid policy file:")
                for e in errors:
                    typer.echo(f"  - {e}")
                raise typer.Exit(2)
            _effective = resolve_effective_policy(policy_data)
            typer.echo(f"Policy file valid: {policy_data['name']} (extends: {policy_data['extends']})")

        elif action == "show":
            if policy_file:
                from sayane.core.policy_file import load_and_validate, resolve_effective_policy
                policy_data, errors = load_and_validate(policy_file)
                if errors:
                    for e in errors:
                        typer.echo(f"Error: {e}", err=True)
                    raise typer.Exit(2)
                effective = resolve_effective_policy(policy_data)
                if effective:
                    typer.echo(_json.dumps(effective, ensure_ascii=False, indent=2))
                return

            if not profile_name:
                raise typer.BadParameter("profile name or --file required for 'show'")
            profile = get_policy(profile_name)
            if profile is None:
                typer.echo(f"Unknown policy: {profile_name}")
                return
            typer.echo(_json.dumps(profile, ensure_ascii=False, indent=2))
            return

        raise typer.BadParameter(f"Unknown action: {action}")

    @app.command()
    def key(
        action: Annotated[str, typer.Argument(help="generate | list")],
    ) -> None:
        """Generate or list Ed25519 signing keys (Phase 16)."""
        from sayane.core.signing import generate_keypair, list_keys

        if action == "generate":
            info = generate_keypair()
            typer.echo(f"Key generated: {info['key_id']}")
            typer.echo(f"  Private: {info['private_key_path']}")
            typer.echo(f"  Public:  {info['public_key_path']}")
        elif action == "list":
            keys = list_keys()
            if not keys:
                typer.echo("No keys found.")
            for k in keys:
                typer.echo(f"  {k['key_id']} (private: {k['has_private']})")
        else:
            raise typer.BadParameter(f"Unknown action: {action}")

    @app.command()
    def sign(
        bundle_path: Annotated[Path, typer.Argument(help="Bundle to sign.")],
        key_id: Annotated[str | None, typer.Option("--key", help="Key ID to sign with.")] = None,
    ) -> None:
        """Sign a context bundle (Phase 16)."""
        from sayane.core.import_bundle import parse_bundle
        from sayane.core.signing import sign_data, signed_payload_for_bundle, list_keys, verify_signature
        import yaml as _yaml

        if key_id is None:
            keys = list_keys()
            priv_keys = [k for k in keys if k["has_private"] == "True"]
            if not priv_keys:
                raise typer.BadParameter("No private keys found. Run 'sayane key generate' first.")
            key_id = priv_keys[0]["key_id"]

        parsed = parse_bundle(bundle_path)
        if parsed is None:
            raise typer.BadParameter(f"Could not parse bundle: {bundle_path}")

        signed = sign_data(parsed, key_id, payload_fn=signed_payload_for_bundle)
        bundle_path.write_text(_yaml.safe_dump(signed, allow_unicode=True, sort_keys=False), encoding="utf-8")
        result = verify_signature(signed, payload_fn=signed_payload_for_bundle)
        typer.echo(f"Bundle signed: {key_id} → status: {result['status']}")

    @app.command()
    def package(
        action: Annotated[str, typer.Argument(help="create | inspect | verify | preview")],
        path: Annotated[Path | None, typer.Argument()] = None,
        output: Annotated[Path, typer.Option("--output", "-o", help="Output directory.")] = Path("./sayane-export-package"),
        bundle: Annotated[Path | None, typer.Option("--bundle", help="Context bundle.")] = None,
        audit_export: Annotated[Path | None, typer.Option("--audit-export", help="Audit export file.")] = None,
        transfer_report: Annotated[Path | None, typer.Option("--transfer-report", help="Transfer report file.")] = None,
        policy_file: Annotated[Path | None, typer.Option("--policy-file", help="Policy file.")] = None,
        sign: Annotated[bool, typer.Option("--sign")] = False,
    ) -> None:
        """Create, inspect, or verify a signed export package (Phase 17)."""
        from sayane.core.export_package import create_package, inspect_package, verify_package

        if action == "create":
            artifacts: dict[str, Path] = {}
            if bundle:
                artifacts["bundle"] = bundle
            if audit_export:
                artifacts["audit"] = audit_export
            if transfer_report:
                artifacts["report"] = transfer_report
            if policy_file:
                artifacts["policy"] = policy_file

            manifest = create_package(
                output_dir=output,
                artifacts={k: v for k, v in artifacts.items() if v},
                sign=sign,
            )
            typer.echo(f"Package created: {output}")
            typer.echo(f"  Package ID: {manifest.get('package_id')}")
            typer.echo(f"  Artifacts: {manifest.get('summary', {}).get('artifact_count', 0)}")

        elif action == "inspect":
            pkg_dir = path or Path(".")
            manifest = inspect_package(pkg_dir)
            if manifest is None:
                typer.echo("Manifest missing or invalid.")
                return
            typer.echo(f"Package: {manifest.get('package_id')}")
            for art in manifest.get("artifacts", []):
                sig = art.get("signature", {}).get("status", "?")
                typer.echo(f"  {art['role']}: {art['path']} (sig: {sig})")

        elif action == "verify":
            pkg_dir = path or Path(".")
            result = verify_package(pkg_dir)
            typer.echo(f"Package verification: {result['status']}")
            for e in result["errors"]:
                typer.echo(f"  Error: {e}")
            for w in result["warnings"]:
                typer.echo(f"  Warning: {w}")

        elif action == "preview":
            pkg_dir = path or Path(".")
            from sayane.core.export_package import preview_package, render_preview_text
            preview = preview_package(pkg_dir)
            typer.echo(render_preview_text(preview))

        else:
            raise typer.BadParameter(f"Unknown action: {action}")
