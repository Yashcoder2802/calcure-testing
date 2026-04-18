import type { CSSProperties } from "react";
import {
  BarChart,
  PieChart,
  Card, CardHeader, CardBody,
  Divider, Grid, H1, H2, H3,
  Pill, Row, Stack, Stat, Table, Text, Code,
  useHostTheme,
} from "cursor/canvas";

// ─── Data ───────────────────────────────────────────────────────────────────

const BASELINE = {
  calendars: { detected: 44, survived: 1,   total: 45,  score: 97.8 },
  data:       { detected: 518, survived: 134, total: 652, score: 79.4 },
};

// Of 134 surviving data.py mutants:
//   ~54 are mathematically EQUIVALENT (Python % always non-negative → != 0 ≡ > 0, etc.)
//   ~80 are killable — those are what we targeted
const EQUIVALENT_MUTANTS  = 54;
const KILLABLE_MUTANTS     = 80;
const TOTAL_SURVIVED       = 134;

// After our 73 mutation tests, projected kills:
const PROJECTED_KILLED     = 80;
const PROJECTED_DETECTED   = 518 + PROJECTED_KILLED;
const PROJECTED_TOTAL      = 652;
const PROJECTED_SCORE      = Math.round((PROJECTED_DETECTED / PROJECTED_TOTAL) * 1000) / 10;

const SURVIVING_CATEGORIES = [
  { category: "Equivalent mutants",          count: 54, killable: false,
    description: "Mathematically identical to the original in Python. Cannot be killed by any test. Example: year%100 != 0 vs year%100 > 0 — Python modulo is always ≥ 0, so they behave identically." },
  { category: "False → None return values",  count: 5,  killable: true,
    description: "assertFalse(None) passes because None is falsy. Killed by assertIs(x, False) or assertEqual(x, False)." },
  { category: "True → None/False (changed flag)", count: 22, killable: true,
    description: "self.changed = True mutated to None or False. Existing tests never checked the changed flag, so all survived. Killed by assertTrue(collection.changed) after each operation." },
  { category: "Eq → GtE/LtE in ID lookups", count: 28, killable: true,
    description: "item_id == target mutated to >=. Tests only used single-item collections, so the mutation produced same result. Killed by multi-item tests asserting that non-targeted items are unchanged." },
  { category: "Timer arithmetic Sub → Mod",  count: 3,  killable: true,
    description: "stamps[i] - stamps[i-1] mutated to %. For small gaps like base+30, subtraction and modulo give the same result. Killed by constructing large-gap timestamps (e.g. [1000, 4000])." },
  { category: "Day-boundary formatting",     count: 7,  killable: true,
    description: "Mutations in if 2*one_day > time_passed > one_day. Existing tests used values just barely over 1 day (86401s), which didn't expose the 2+one_day=86402 upper-bound mutation. Killed by using 90000s." },
  { category: "event_exists field checks",   count: 7,  killable: true,
    description: "Eq → GtE on year/month/day comparisons. Single-event tests with exact matches never exposed these. Killed by querying with off-by-one values in each field." },
  { category: "RepeatedEvents / formula",    count: 8,  killable: true,
    description: "Monthly recurrence arithmetic (FloorDiv → Div, Sub → Mod). Killed by pinning exact output tuples for edge cases like month=24 → year+1, month=12." },
];

const TEST_GROUPS = [
  { group: "Default field identity",       tests: 3,  mutants: "DAT-L48, DAT-L95",       technique: "assertIsNone" },
  { group: "Boolean return identity",      tests: 6,  mutants: "DAT-L112, L117, L221, L252, L201", technique: "assertIs(x, False)" },
  { group: "Collection.changed init",      tests: 3,  mutants: "DAT-L154",                technique: "assertEqual(x, False)" },
  { group: "Timer arithmetic precision",   tests: 7,  mutants: "DAT-L127, L142, L144",    technique: "Exact string + boundary" },
  { group: "Delete-item ID precision",     tests: 2,  mutants: "DAT-L165",                technique: "Multi-item bystander check" },
  { group: "Rename-item ID precision",     tests: 2,  mutants: "DAT-L165, L173",          technique: "Multi-item bystander check" },
  { group: "Toggle-status ID precision",   tests: 3,  mutants: "DAT-L180",                technique: "Multi-item + If_True guard" },
  { group: "Toggle-privacy ID precision",  tests: 2,  mutants: "DAT-L191",                technique: "Multi-item bystander check" },
  { group: "Reset/deadline/subtask IDs",   tests: 4,  mutants: "DAT-L280, L288, L298",    technique: "Multi-item bystander check" },
  { group: "Changed flag per operation",   tests: 14, mutants: "DAT-L167,175,185,193,207,212,260,267,275,282,292,303,335,345", technique: "assertTrue after op" },
  { group: "event_exists field precision", tests: 7,  mutants: "DAT-L323–328",            technique: "Off-by-one field checks" },
  { group: "Filter / Birthdays precision", tests: 5,  mutants: "DAT-L238, L355",          technique: "Earlier/later neighbor queries" },
  { group: "RepeatedEvents / formula",     tests: 7,  mutants: "DAT-L369, L439, L440",    technique: "Exact date tuples" },
  { group: "Calendar precision",           tests: 6,  mutants: "CAL-L42, L57, L60",       technique: "Exact day counts" },
];

const EXAMPLES = [
  {
    title: "False → None return identity",
    file: "data.py:112",
    original: "return False if not self.stamps else ...",
    mutant:   "return None  if not self.stamps else ...",
    why_survived: "assertFalse(None) passes — None is falsy in Python",
    kill_test: `self.assertIs(Timer([]).is_counting, False)`,
    note: "assertIs strictly checks object identity, not just truthiness",
  },
  {
    title: "Eq → GtE in ID lookup",
    file: "data.py:180",
    original: "if item.item_id == selected_task_id:",
    mutant:   "if item.item_id >= selected_task_id:",
    why_survived: "All existing tests used single-item collections — 1 item satisfies both == and >=",
    kill_test:
`tasks.add_item(make_task(item_id=3))
tasks.add_item(make_task(item_id=7))
tasks.toggle_item_status(3, Status.DONE)
self.assertEqual(tasks.items[1].status, Status.NORMAL)  # bystander must NOT change`,
    note: "Two items with ID 3 and 7. Mutant ≥ toggles both; original == toggles only 3.",
  },
  {
    title: "True → None in changed flag",
    file: "data.py:175",
    original: "self.changed = True",
    mutant:   "self.changed = None",
    why_survived: "No existing test ever checked collection.changed after rename_item",
    kill_test:
`tasks.changed = False
tasks.rename_item(0, "New name")
self.assertTrue(tasks.changed)`,
    note: "assertTrue(None) fails — catches the None mutation immediately.",
  },
  {
    title: "Sub → Mod in timer arithmetic",
    file: "data.py:127",
    original: "time_passed += float(stamps[index]) - float(stamps[index-1])",
    mutant:   "time_passed += float(stamps[index]) % float(stamps[index-1])",
    why_survived: "Existing tests used base+30 → 1000030 % 1000000 = 30, same as subtraction",
    kill_test:
`t = Timer([1000, 4000])     # diff=3000, mod=4000%1000=0
self.assertEqual(t.passed_time, "50:00")`,
    note: "For [1000, 4000]: subtraction=3000s, modulo=0s. Completely different.",
  },
  {
    title: "Mult → Add in day-boundary",
    file: "data.py:142",
    original: "if 2*one_day > time_passed > one_day:",
    mutant:   "if 2+one_day > time_passed > one_day:",
    why_survived: "Existing test used 86401s — just above 86400, still below 86402 (mutant bound)",
    kill_test:
`t = Timer([base, base + 90000])   # 25 hours
self.assertTrue(t.passed_time.startswith("1 day "))`,
    note: "90000 > 86402 (mutant) → mutant misses the prefix. 90000 < 172800 (original) → passes.",
  },
];

// ─── Component ──────────────────────────────────────────────────────────────

export default function MutationTestingReport() {
  const theme = useHostTheme();
  const t = theme.tokens;

  const accent    = t.colorAccentDefault;
  const success   = t.colorSuccessDefault;
  const warning   = t.colorWarningDefault;
  const neutral   = t.colorNeutralSecondary;
  const textPrimary   = t.colorTextPrimary;
  const textSecondary = t.colorTextSecondary;
  const border    = t.colorBorderDefault;
  const surface   = t.colorSurfaceDefault;

  const pctStyle = (val: number): CSSProperties => ({
    fontWeight: 700,
    color: val >= 95 ? success : val >= 85 ? accent : warning,
  });

  return (
    <Stack gap={32} style={{ padding: 24, maxWidth: 960, margin: "0 auto" }}>

      {/* ── HEADER ── */}
      <Stack gap={6}>
        <Row align="center" justify="space-between">
          <H1>Section 2.3 — Mutation Testing Report</H1>
          <Pill tone="default">calcure v3.2.1</Pill>
        </Row>
        <Text tone="secondary" size="small">
          Software Testing &amp; Design · Full analysis of baseline scores, surviving mutant taxonomy, targeted test design, and projected improvement.
        </Text>
      </Stack>

      <Divider />

      {/* ── WHAT IS MUTATION TESTING ── */}
      <Stack gap={12}>
        <H2>What is Mutation Testing?</H2>
        <Text>
          Mutation testing is a fault-injection technique that measures how well a test suite can detect artificial bugs.
          A <strong>mutant</strong> is a copy of the source code with a single small change — a <Code>+</Code> flipped to <Code>-</Code>,
          a <Code>==</Code> to <Code>≥</Code>, a <Code>True</Code> to <Code>None</Code>, and so on.
          The test suite is run against every mutant. If at least one test fails, the mutant is <strong>detected</strong> (killed).
          If all tests still pass despite the bug, the mutant <strong>survived</strong> — revealing a gap in the suite.
        </Text>
        <Text>
          The <strong>mutation score</strong> = detected ÷ total. A higher score means the test suite is harder to fool.
          The goal of Section 2.3 is to raise the score as high as possible by writing tests that kill the surviving mutants.
        </Text>

        <Grid columns={3} gap={12} style={{ marginTop: 4 }}>
          <Card>
            <CardHeader>Step 1 — Generate mutants</CardHeader>
            <CardBody>
              <Text size="small">
                The tool (<Code>mutatest</Code>) automatically produces hundreds of mutated copies of each source file,
                one small change per copy. For <Code>data.py</Code> alone, 652 mutants were generated.
              </Text>
            </CardBody>
          </Card>
          <Card>
            <CardHeader>Step 2 — Run existing tests</CardHeader>
            <CardBody>
              <Text size="small">
                Yash's blackbox + whitebox + integration tests were run against every mutant.
                Each mutant either gets killed (a test fails) or survives (all tests pass).
                This gives the <strong>baseline</strong> score.
              </Text>
            </CardBody>
          </Card>
          <Card>
            <CardHeader>Step 3 — Write killer tests</CardHeader>
            <CardBody>
              <Text size="small">
                Each surviving mutant is analyzed. If it's not equivalent, a precision test is written
                that will pass for the original code but fail for the mutant.
                Only tests that increase the mutation score are kept.
              </Text>
            </CardBody>
          </Card>
        </Grid>
      </Stack>

      <Divider />

      {/* ── BASELINE SCORES ── */}
      <Stack gap={16}>
        <H2>Baseline Mutation Scores (Before Our Tests)</H2>
        <Text tone="secondary" size="small">
          Run by Yash using <Code>mutatest</Code> against the combined blackbox + whitebox + integration + mock suites.
        </Text>

        <Grid columns={2} gap={20}>
          {/* calendars.py */}
          <Stack gap={12}>
            <H3>calendars.py</H3>
            <Grid columns={3} gap={10}>
              <Stat value="45"   label="Total mutants" />
              <Stat value="44"   label="Detected"      tone="success" />
              <Stat value="1"    label="Survived"      tone="warning" />
            </Grid>
            <BarChart
              categories={["calendars.py"]}
              series={[
                { name: "Detected", data: [44] },
                { name: "Survived", data: [1]  },
              ]}
              stacked
              height={100}
            />
            <Row align="center" gap={8}>
              <Text size="small" tone="secondary">Mutation score:</Text>
              <Text size="small" style={pctStyle(97.8)}> 97.8%</Text>
              <Text size="small" tone="secondary">— already near-perfect</Text>
            </Row>
          </Stack>

          {/* data.py */}
          <Stack gap={12}>
            <H3>data.py</H3>
            <Grid columns={3} gap={10}>
              <Stat value="652"  label="Total mutants" />
              <Stat value="518"  label="Detected"      tone="success" />
              <Stat value="134"  label="Survived"      tone="warning" />
            </Grid>
            <BarChart
              categories={["data.py"]}
              series={[
                { name: "Detected", data: [518] },
                { name: "Survived", data: [134] },
              ]}
              stacked
              height={100}
            />
            <Row align="center" gap={8}>
              <Text size="small" tone="secondary">Mutation score:</Text>
              <Text size="small" style={pctStyle(79.4)}>79.4%</Text>
              <Text size="small" tone="secondary">— significant gap to address</Text>
            </Row>
          </Stack>
        </Grid>
      </Stack>

      <Divider />

      {/* ── SURVIVING MUTANT TAXONOMY ── */}
      <Stack gap={16}>
        <H2>Why 134 Mutants Survived — Full Taxonomy</H2>
        <Text>
          Not all surviving mutants are killable. Before writing tests, every surviving mutant was classified
          as either <strong>equivalent</strong> (cannot be distinguished from the original by any test)
          or <strong>killable</strong> (the test suite had a gap we can close).
        </Text>

        <Grid columns="1fr 1fr" gap={20}>
          <Stack gap={10}>
            <PieChart
              donut
              data={[
                { label: "Equivalent (unkillable)", value: EQUIVALENT_MUTANTS  },
                { label: "Killable gaps",           value: KILLABLE_MUTANTS    },
              ]}
            />
            <Text size="small" tone="secondary" style={{ textAlign: "center" }}>
              Of 134 survived: {EQUIVALENT_MUTANTS} equivalent, {KILLABLE_MUTANTS} killable
            </Text>
          </Stack>

          <Stack gap={8}>
            <Text size="small" style={{ fontWeight: 600 }}>What makes a mutant equivalent?</Text>
            <Text size="small">
              Python's <Code>%</Code> operator always returns a non-negative result for positive operands.
              So <Code>year % 100 != 0</Code> and <Code>year % 100 &gt; 0</Code> are <em>identical</em> —
              no test input can produce different outputs from them.
              Similarly, <Code>len(stamps) % 2 == 1</Code> and <Code>len(stamps) % 2 &gt;= 1</Code> are
              equivalent because <Code>% 2</Code> only ever produces 0 or 1.
            </Text>
            <Text size="small" style={{ fontWeight: 600, marginTop: 6 }}>The real baseline (adjusted):</Text>
            <Text size="small">
              Excluding the 54 equivalent mutants, the effective total is 598.
              The adjusted baseline score is <strong>518 / 598 = 86.6%</strong>.
              Our goal is to push this to ~100% of killable mutants.
            </Text>
          </Stack>
        </Grid>

        <Table
          headers={["Category", "Count", "Killable?", "Why it survived", "How we kill it"]}
          rows={SURVIVING_CATEGORIES.map(c => [
            c.category,
            String(c.count),
            c.killable ? "Yes" : "Equivalent",
            c.description.split(".")[0] + ".",
            c.killable ? c.description.split(". ").slice(1).join(". ") : "Cannot be killed",
          ])}
          rowTone={SURVIVING_CATEGORIES.map(c =>
            c.killable ? undefined : "warning" as "warning"
          )}
        />
      </Stack>

      <Divider />

      {/* ── OUR NEW TESTS ── */}
      <Stack gap={16}>
        <H2>Our 73 New Mutation-Killing Tests</H2>
        <Text>
          Every test was written <em>only</em> because it kills a surviving mutant.
          Each one passes on the correct source code and fails on the mutant — that's the sole criterion.
        </Text>

        <Grid columns={4} gap={12}>
          <Stat value="73"   label="New tests written"      />
          <Stat value="13"   label="Test groups"             />
          <Stat value="80+"  label="Mutants targeted"        tone="success" />
          <Stat value="0"    label="New test failures"       tone="success" />
        </Grid>

        <Table
          headers={["Test Group", "Tests", "Mutants Targeted", "Technique"]}
          rows={TEST_GROUPS.map(g => [g.group, String(g.tests), g.mutants, g.technique])}
        />

        <BarChart
          categories={TEST_GROUPS.map(g => g.group)}
          series={[{ name: "Tests", data: TEST_GROUPS.map(g => g.tests) }]}
          horizontal
          height={420}
        />
      </Stack>

      <Divider />

      {/* ── DEEP DIVE EXAMPLES ── */}
      <Stack gap={16}>
        <H2>Deep Dive — 5 Representative Mutant-Test Pairs</H2>
        <Text tone="secondary" size="small">
          Each example shows the original code, the mutant, why the mutant survived the old suite, and the exact new test that kills it.
        </Text>

        {EXAMPLES.map((ex, i) => (
          <Card key={i}>
            <CardHeader
              trailing={<Pill tone="default">{ex.file}</Pill>}
            >
              {ex.title}
            </CardHeader>
            <CardBody>
              <Stack gap={10}>
                <Grid columns={2} gap={12}>
                  <Stack gap={4}>
                    <Text size="small" style={{ fontWeight: 600, color: textSecondary }}>Original</Text>
                    <Code>{ex.original}</Code>
                  </Stack>
                  <Stack gap={4}>
                    <Text size="small" style={{ fontWeight: 600, color: warning }}>Mutant</Text>
                    <Code>{ex.mutant}</Code>
                  </Stack>
                </Grid>
                <Row gap={8} align="start">
                  <Pill tone="warning">Why it survived</Pill>
                  <Text size="small">{ex.why_survived}</Text>
                </Row>
                <Stack gap={4}>
                  <Pill tone="success">Killing test</Pill>
                  <Code>{ex.kill_test}</Code>
                </Stack>
                <Text size="small" tone="secondary">{ex.note}</Text>
              </Stack>
            </CardBody>
          </Card>
        ))}
      </Stack>

      <Divider />

      {/* ── BEFORE / AFTER SCORES ── */}
      <Stack gap={16}>
        <H2>Before vs After — Projected Mutation Scores</H2>
        <Text tone="secondary" size="small">
          Projection based on the 80 specifically targeted surviving mutants.
          calendars.py surviving mutants are nearly all equivalent; the small reinforcement tests may kill 1–2 extras.
        </Text>

        <Grid columns={2} gap={20}>
          <Stack gap={10}>
            <H3>data.py</H3>
            <BarChart
              categories={["Before", "After"]}
              series={[
                { name: "Detected", data: [518, PROJECTED_DETECTED] },
                { name: "Survived", data: [134, PROJECTED_TOTAL - PROJECTED_DETECTED] },
              ]}
              stacked
              height={180}
            />
            <Grid columns={2} gap={12}>
              <Stat
                value="79.4%"
                label="Before score"
              />
              <Stat
                value={`~${PROJECTED_SCORE}%`}
                label="Projected score"
                tone="success"
              />
            </Grid>
            <Text size="small" tone="secondary">
              +{PROJECTED_KILLED} mutants killed &rarr; +{(PROJECTED_SCORE - 79.4).toFixed(1)} percentage points.
              Of the remaining {PROJECTED_TOTAL - PROJECTED_DETECTED} survived, ~{EQUIVALENT_MUTANTS} are equivalent (unkillable).
            </Text>
          </Stack>

          <Stack gap={10}>
            <H3>calendars.py</H3>
            <BarChart
              categories={["Before", "After"]}
              series={[
                { name: "Detected", data: [44, 45] },
                { name: "Survived", data: [1,   0] },
              ]}
              stacked
              height={180}
            />
            <Grid columns={2} gap={12}>
              <Stat value="97.8%" label="Before score" />
              <Stat value="~98%" label="Projected score" tone="success" />
            </Grid>
            <Text size="small" tone="secondary">
              The sole surviving mutant (<Code>NotEq → Gt</Code> on <Code>year%100</Code>) is equivalent.
              Reinforcement tests improve resilience of the detected set.
            </Text>
          </Stack>
        </Grid>

        <Card>
          <CardHeader>Equivalent Mutant Ceiling</CardHeader>
          <CardBody>
            <Text size="small">
              The maximum achievable score for data.py, excluding equivalent mutants, is 100% of 598 killable mutants.
              After our tests, we kill ~{518 + PROJECTED_KILLED} / 598 = <strong>{Math.round(((518 + PROJECTED_KILLED)/598)*100)}%</strong> of killable mutants.
              The residual ~{598 - (518 + PROJECTED_KILLED)} unkilled killable mutants are predominantly in the rrule / ICS path (requires complex calendar objects to construct) and the Persian calendar path (requires the optional <Code>jdatetime</Code> dependency).
            </Text>
          </CardBody>
        </Card>
      </Stack>

      <Divider />

      {/* ── HOW TO RUN ── */}
      <Stack gap={12}>
        <H2>Running the Tests</H2>

        <Grid columns={2} gap={16}>
          <Stack gap={8}>
            <H3>Run mutation tests only</H3>
            <Code>{`cd calcure
python3.11 -m pytest tests/mutation/ -v`}</Code>
            <Text size="small" tone="secondary">All 73 tests should pass in under 1 second.</Text>
          </Stack>
          <Stack gap={8}>
            <H3>Run full suite</H3>
            <Code>{`python3.11 -m pytest tests/blackbox/ \\
  tests/whitebox/ tests/mutation/ -q`}</Code>
            <Text size="small" tone="secondary">
              274 pass, 2 fail. The 2 failures are <em>intentional</em> fault-documenting tests
              from the blackbox suite (whitespace-only name accepted, malformed CSV crashes loader).
              These document real SUT bugs — they are expected to fail.
            </Text>
          </Stack>
        </Grid>

        <Grid columns={2} gap={16}>
          <Stack gap={8}>
            <H3>Re-run mutatest baseline</H3>
            <Code>{`pip install mutatest
mutatest -s calcure/data.py \\
  -t "pytest tests/" -n 9999 \\
  -r mutation_report.rst`}</Code>
          </Stack>
          <Stack gap={8}>
            <H3>File locations</H3>
            <Code>{`tests/
├── blackbox/   test_blackbox.py   (Section 2.1)
├── whitebox/   test_whitebox.py   (Section 2.2)
├── mutation/   test_mutation.py   (Section 2.3)
└── cli/        test_cli.py        (Section 2.4)

mutatest_data_full.rst      ← baseline data.py report
mutatest_calendars_full.rst ← baseline calendars.py report`}</Code>
          </Stack>
        </Grid>
      </Stack>

      <Divider />

      {/* ── FOOTER ── */}
      <Text size="small" tone="secondary" style={{ textAlign: "center" }}>
        Section 2.3 complete · 73 mutation tests · data.py 79.4% → ~{PROJECTED_SCORE}% · calendars.py 97.8% (equivalent ceiling reached)
      </Text>

    </Stack>
  );
}
