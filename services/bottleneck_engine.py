"""
Bottleneck Engine — Analyzes warehouse operations to identify bottlenecks.
"""
from database import db
from database.models import PickTask, PackTask, QualityCheck, Order


class BottleneckEngine:

    def analyze(self) -> dict:
        """Analyze operational metrics and identify bottleneck."""
        pick_avg = self._avg_minutes(PickTask, "pick")
        pack_avg = self._avg_minutes(PackTask, "pack")
        qc_avg = self._avg_minutes_qc()

        stages = {
            "PICKING": {"avg_minutes": pick_avg, "label": "Picking"},
            "PACKING": {"avg_minutes": pack_avg, "label": "Packing"},
            "QUALITY_CHECK": {"avg_minutes": qc_avg, "label": "Quality Check"},
        }

        # Identify bottleneck as the slowest stage
        bottleneck_stage = max(stages, key=lambda s: stages[s]["avg_minutes"])
        bottleneck_info = stages[bottleneck_stage]

        # Count tasks in each stage
        stage_counts = {
            "PICKING": PickTask.query.filter_by(status="IN_PROGRESS").count(),
            "PACKING": PackTask.query.filter_by(status="IN_PROGRESS").count(),
            "QUALITY_CHECK": QualityCheck.query.filter_by(status="PENDING").count(),
        }

        recommendation = self._build_recommendation(bottleneck_stage, bottleneck_info, stage_counts)

        return {
            "bottleneck_stage": bottleneck_stage,
            "bottleneck_label": bottleneck_info["label"],
            "avg_minutes": bottleneck_info["avg_minutes"],
            "stages": {
                k: {**v, "active_tasks": stage_counts[k]}
                for k, v in stages.items()
            },
            "recommendation": recommendation,
            "impact": self._assess_impact(bottleneck_stage, stage_counts),
        }

    def _avg_minutes(self, model, mode: str) -> float:
        tasks = model.query.filter_by(status="COMPLETED").filter(
            model.started_at.isnot(None),
            model.completed_at.isnot(None),
        ).all()
        if not tasks:
            return {"pick": 12.0, "pack": 25.0}[mode]
        times = [(t.completed_at - t.started_at).total_seconds() / 60 for t in tasks]
        return round(sum(times) / len(times), 1)

    def _avg_minutes_qc(self) -> float:
        checks = QualityCheck.query.filter(
            QualityCheck.checked_at.isnot(None),
            QualityCheck.status.in_(["PASSED", "FAILED"]),
        ).all()
        if not checks:
            return 8.0
        # QC doesn't have started_at, estimate 8 min average
        return 8.0

    def _build_recommendation(self, stage: str, info: dict, counts: dict) -> str:
        avg = info["avg_minutes"]

        if stage == "PICKING":
            return (
                f"Picking is the current bottleneck (avg {avg:.1f} min/task). "
                f"Recommend: Optimize bin locations, add 1-2 pickers, "
                f"review zone layout to reduce travel distance."
            )
        elif stage == "PACKING":
            return (
                f"Packing is the current bottleneck (avg {avg:.1f} min/task). "
                f"Recommend: Move available workers from Picking to Packing, "
                f"add a packing station, review packing materials availability."
            )
        elif stage == "QUALITY_CHECK":
            return (
                f"Quality Check is the current bottleneck (avg {avg:.1f} min/check). "
                f"Recommend: Add another QC inspector, implement pre-check verification at packing."
            )
        return "No significant bottleneck detected."

    def _assess_impact(self, stage: str, counts: dict) -> str:
        active = counts.get(stage, 0)
        if active > 5:
            return f"HIGH — {active} active tasks queued. Immediate action required."
        elif active > 2:
            return f"MEDIUM — {active} active tasks. Monitor closely."
        elif active > 0:
            return f"LOW — {active} active tasks. Normal processing."
        return "MINIMAL — No active tasks in this stage."
