"""Original, compact Big Five-style MVP assessment catalog."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment, Question, Trait

CATALOG = (
    (Trait.OPENNESS, False, "I enjoy exploring ideas that are unfamiliar to me."),
    (Trait.OPENNESS, True, "I prefer routines over trying new approaches."),
    (Trait.OPENNESS, False, "I notice interesting connections between different topics."),
    (Trait.OPENNESS, True, "I rarely look for creative ways to solve a problem."),
    (Trait.CONSCIENTIOUSNESS, False, "I plan important tasks before I begin them."),
    (Trait.CONSCIENTIOUSNESS, True, "I often leave small responsibilities unfinished."),
    (Trait.CONSCIENTIOUSNESS, False, "I keep working when a task needs careful attention."),
    (Trait.CONSCIENTIOUSNESS, True, "I find it difficult to keep track of deadlines."),
    (Trait.EXTRAVERSION, False, "I feel energised by contributing to group discussions."),
    (Trait.EXTRAVERSION, True, "I usually avoid starting conversations with new people."),
    (Trait.EXTRAVERSION, False, "I am comfortable sharing my point of view with others."),
    (Trait.EXTRAVERSION, True, "I tend to stay in the background during social activities."),
    (Trait.AGREEABLENESS, False, "I try to understand another person's perspective during disagreement."),
    (Trait.AGREEABLENESS, True, "I can be dismissive when someone disagrees with me."),
    (Trait.AGREEABLENESS, False, "I offer help when I see a classmate struggling."),
    (Trait.AGREEABLENESS, True, "I focus on winning an argument more than listening."),
    (Trait.NEUROTICISM, True, "I generally recover quickly after a stressful moment."),
    (Trait.NEUROTICISM, False, "Small uncertainties can stay on my mind for a long time."),
    (Trait.NEUROTICISM, False, "I often feel tense when several tasks compete for attention."),
    (Trait.NEUROTICISM, True, "I usually feel calm when plans change unexpectedly."),
)


def ensure_default_assessment(database: Session) -> None:
    """Create the sole Day 3 assessment once, without duplicating it on restart."""
    if database.scalar(select(Assessment).where(Assessment.title == "MindTrace Student Profile")):
        return
    assessment = Assessment(
        title="MindTrace Student Profile",
        description="A short original Big Five-style self-reflection assessment using a 1–5 scale.",
    )
    database.add(assessment)
    database.flush()
    database.add_all(
        Question(assessment_id=assessment.id, trait=trait, reverse_scored=reverse, question_text=text, order=index)
        for index, (trait, reverse, text) in enumerate(CATALOG, start=1)
    )
    database.commit()
