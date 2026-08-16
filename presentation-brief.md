# Presentation brief — Trades Directory database project

**This is a content brief, not a deck.** Hand it to a designer (or to Claude) to
build the slides from. Every fact in it has been verified against the running
system; nothing here is aspirational.

**Project in one line:** a directory of Egyptian tradesmen and contracting
shops, organised by trade (بند), built on PostgreSQL with a FastAPI web app on
top.

**Team:** Mohamed Magdy (database), Wageh Mohamed Ali (backend), Bola Emil (frontend).

**Suggested length:** 13 slides, ~15 minutes.
**Language:** slide text in Arabic, technical terms and code in English. The app
and data are Arabic-first (RTL).

---

## Assets to hand over

### Files — all under `~/db-project/`

| File | Use it for |
|---|---|
| `presentation-assets/00-erd.png` | The ER diagram. Slide 5. |
| `presentation-assets/01-home.png` | Home page, 7 categories. Slides 1, 9. |
| `presentation-assets/02-search.png` | Search results for «سباك». Slide 9. |
| `presentation-assets/03-trade.png` | Shops within one trade. Slide 8. |
| `presentation-assets/04-shop.png` | **One shop page showing all five tables at once** — the shop, its trades, its branches, and the employees inside each branch. The strongest single image in the set. Slides 6, 8, 14. |
| `presentation-assets/05-add-shop.png` | The add-shop form. Slide 10. |
| `presentation-assets/06-add-branch.png` | The add-branch form. Slide 10. |
| `presentation-assets/07-api-docs.png` | Auto-generated API docs at `/docs`. Slide 8. |
| `presentation-assets/psql-outputs.txt` | Real terminal output — table list, full `\d branch`, row counts, three rejected inserts, the three-table join. **The single most useful asset in here.** |
| `schema.sql` | 33 lines. Slides 4–5. |
| `seed.sql` | 60 lines. Slide 11. |
| `queries.sql` | 56 lines. Slides 6–7. |
| `ENDPOINTS.md` | The route contract. Slide 8. |
| `app_starter.py` | The web app, 9 route handlers. Slide 8. |
| `erd.dot` / `erd.dbml` | Diagram sources, if the ERD needs redrawing. |

### Links

| Link | Use it for |
|---|---|
| https://github.com/Mo7ammedMajdy/trades-directory | The repository. Slide 13. |
| https://github.com/Mo7ammedMajdy/trades-directory/issues?q=is%3Aissue | All 7 issues, closed, each assigned. Slide 12. |
| https://claude.ai/code/artifact/a8c67faa-9ee0-4c4b-9aef-3c24e2acf786 | **Join walkthrough** — step-by-step diagrams of how a `JOIN` executes on this data. Slide 7. |
| https://claude.ai/code/artifact/a4e30527-0b59-4fcb-94f2-008ae6300590 | **Join simulator** — steps through all 80 row comparisons live. Slide 7. Best live demo in the deck. |

*(Both artifact links are private to Mohamed's account — open them on his machine, or screen-record them beforehand.)*

### Numbers that recur

- **5 tables**, **55 rows**: 7 trades, 8 shops, 10 shop-trade links, 13 branches, 17 employees
- **9 route handlers**, **4 page templates** plus a shared base
- PostgreSQL **18.4**, FastAPI **0.141.1**
- **7 GitHub issues**, all closed

---

# Slide 1 — Title

**Content**

دليل الحرفيين والأنشطة التجارية — Trades Directory
A searchable directory of tradesmen and contracting shops, organised by trade.

Built on PostgreSQL. Three people, one repository, five tables, 55 rows.

Names and roles: Mohamed (database), Wageh (backend), Bola (frontend).

**Visual / animation**

Screenshot `01-home.png` sliding up from the bottom and settling, slightly
tilted in 3D as a browser mock. Behind it, the seven category names fade in one
by one in Arabic — السباكة، النجارة، الكهرباء، أعمال ميكانيكا، حدادة، أعمال منزلية، نقاشة —
then dissolve into the screenshot. Sets up that everything shown is real and
running.

---

# Slide 2 — The problem: why not just an app with a file?

**Content**

The obvious first instinct is a Java (or Python) program that keeps the data in
memory and saves it to a file. That fails for three specific reasons, and those
three reasons are the entire argument for a database.

**1. Everything lives in RAM, and RAM is temporary.** An in-memory program holds
the whole directory in objects. Close it, and the objects are gone. Saving to a
file means rewriting the whole file each time — and if the program crashes
mid-write, the file is corrupt and *all* the data is lost, not just the last
change. A database writes changes durably, one at a time, and survives a crash
mid-write.

**2. Retrieval is a loop instead of an index.** To find every plumber in Nasr
City, a Java app loads all shops into a list and loops through them comparing
strings — O(n), every row touched, every time. Postgres keeps sorted index
structures and jumps straight to matching rows without reading the rest. At 8
shops nobody notices. At 80,000 the loop becomes the entire program.

**3. Nothing enforces the rules.** In a Java app, "a branch must belong to a real
shop" is a comment, or a check someone remembers to write. In the database it is
a `FOREIGN KEY`, enforced on every insert from every direction, forever — and no
code path can bypass it.

**The one-sentence version:** an app *remembers* data; a database *guarantees* it.

**Visual / animation**

Split screen. Left, labelled «تطبيق عادي»: a stack of RAM boxes holding rows; a
"crash" flash; the boxes vanish; a spinner scans rows one by one, top to bottom.
Right, labelled «قاعدة بيانات»: rows drop onto a disk platter and stay lit; a
query arrow jumps *directly* to row 5,000 skipping everything between. Both
sides animate at once so the contrast is unmissable.

---

# Slide 3 — Why PostgreSQL and not SQLite

**Content**

SQLite was the alternative worth considering — zero install, one file. We chose
Postgres for four reasons, in order of how much they matter to this project.

**1. Concurrent writers.** SQLite locks the entire database file while writing;
a second writer waits. Postgres uses MVCC (multi-version concurrency control),
so many people can read and write at the same time without blocking each other.
A directory that several branch managers update simultaneously needs that; a
single-user file does not.

**2. Real types and real constraints.** SQLite has dynamic typing — put the text
`"hello"` in an `INTEGER` column and it accepts it. Postgres refuses. Our whole
design leans on the database rejecting bad data, and that only works if the
types are actually enforced.

**3. Server, not a file.** Postgres runs as a service other machines connect to
over the network. SQLite is a file that must be on the same disk as the program.
The moment the app moves to a server and users hit it from browsers, SQLite has
nowhere to live.

**4. It scales along the axis we'd actually grow on.** Indexes, query planning,
partitioning and replication are built in. Same SQL we already wrote — the
`SELECT`s on slide 6 do not change when the table goes from 8 rows to 8 million.

**The honest counterpoint, worth saying out loud:** SQLite would have worked
perfectly for 55 rows. We chose Postgres because it is what the project would
need if it ever left the classroom, and because the SQL skills transfer.

**Visual / animation**

Two columns growing into a comparison table, row by row, each row ticking
green on the Postgres side. Then a scale animation: a single "SQLite" file icon
with one door and a queue of users waiting; beside it a "PostgreSQL" server with
many doors open at once, users flowing through in parallel.

---

# Slide 4 — Designing the schema: what goes in a table

**Content**

The professor's brief listed the categories and the fields to record per shop.
Turning that into tables was the actual design work.

**The rule we used: one table = one kind of thing.** If you cannot finish the
sentence "each row is one ______", it should not be a table.

**Why five tables and not one big one.** A shop with three branches in a single
flat sheet forces you to retype its name, commercial register and bank account
three times. That is not just wasteful:

- Mistype one copy and there are now two contradictory versions of the truth
- Change the bank account and you must find and fix every row; miss one and the data lies
- Nothing stops a branch pointing at a shop that does not exist

Splitting shop facts from branch facts stores each fact **exactly once**.

**The five tables, and which line of the brief each came from:**

| Table | From the brief | Holds |
|---|---|---|
| `trade` | the list of بنود | the 7 categories |
| `shop` | اسم المحل، السجل التجاري، حساب البنك، الطاقة الفنية | the business itself |
| `branch` | الفرع، العنوان، التليفون | each location |
| `employee` | (our addition) | staff at a branch |
| `shop_trade` | — | links shops to trades |

**`shop_trade` is the one table not on the brief, and the one worth defending.**
A single `trade_id` column on `shop` works right up until a shop does two
trades — and شركة الإتقان للصيانة المتكاملة does three. A column holds one value.
So the relationship gets its own table, where facts can multiply. This converts
one many-to-many into two one-to-many relationships, each of which a foreign key
can express perfectly.

**Visual / animation**

Start with one wide spreadsheet, the shop's register and bank number visibly
repeated down three rows, highlighted red. One cell edits itself to a different
value — the red rows now disagree. Then the sheet splits apart: shop columns fly
left into a `shop` box, branch columns fly right into a `branch` box, and a
labelled arrow `shop_id` snaps between them. The duplicated values collapse into
a single row. End on the five boxes settling into the ERD layout.

---

# Slide 5 — The schema in SQL: constraints are the design

**Content**

`schema.sql` is 33 lines. It is the whole structure, and it is the file everyone
else builds against.

Each constraint is a decision about what is allowed to exist:

| Constraint | Means | Why we chose it |
|---|---|---|
| `SERIAL PRIMARY KEY` | auto-numbered identity | never typed by hand, never reused |
| `NOT NULL` | cannot be blank | a shop with no name is meaningless |
| `UNIQUE` | no duplicates | two businesses cannot share a commercial register |
| `CHECK (... ~ '^\+?[0-9]{7,15}$')` | must match this pattern | rejects a phone that isn't a phone |
| `REFERENCES shop(id)` | must point at a real shop | no orphan branches |
| `ON DELETE CASCADE` | children go with the parent | delete a shop, its branches go too |
| `PRIMARY KEY (shop_id, trade_id)` | composite key | the pair *is* the identity; a shop cannot be linked to the same trade twice |

**The decision worth explaining: `commercial_register` is `UNIQUE` but not
`NOT NULL`.** An informal one-man plumber — exactly what the brief listed
alongside shops — has no commercial register. Making it required would make him
impossible to enter. Postgres allows many `NULL`s under a `UNIQUE` constraint,
because two unknowns are not necessarily equal. So every real register is
unique, and unlimited shops can have none.

**A constraint is not "is this usually true?" — it is "am I willing to have the
row rejected?"**

**Visual / animation**

`schema.sql` types itself out, then each constraint keyword highlights in turn
with its plain-Arabic meaning appearing beside it. Then three inserts are typed
into a terminal and each is **rejected**, the real error text appearing in red —
use the exact strings from `psql-outputs.txt` section 4:

```
ERROR:  duplicate key value violates unique constraint "trade_name_en_key"
ERROR:  new row for relation "branch" violates check constraint "branch_phone_number_check"
ERROR:  insert or update on table "branch" violates foreign key constraint "branch_shop_id_fkey"
```

Three rejections in a row is the most persuasive moment available. Land it.

---

# Slide 6 — The ER diagram

**Content**

Five tables, two kinds of relationship, and the difference between them matters.

**Ownership (one-to-many):** `shop → branch → employee`. Each is the parent of
the next. Delete a shop and its branches go; delete a branch and its employees
go. A branch has no meaning without its shop — it is not data to preserve, it is
wreckage.

**Association (many-to-many):** `shop ↔ trade`, through `shop_trade`. Neither
owns the other. A shop can drop a trade and survive; a trade can lose every shop
and still exist.

The crow's foot marks the "many" end. Read it out loud: *one shop has many
branches, one branch employs many people, one shop works in many trades.*

**Visual / animation**

`00-erd.png` fading in, then relationships lighting up one at a time as they are
described — the `shop → branch` line pulses, then `branch → employee`, then both
legs of `shop ↔ trade` through the junction. Finally, a delete animation: strike
out a shop row and watch its branches and their employees grey out and vanish in
sequence, showing `ON DELETE CASCADE` propagating down the chain.

---

# Slide 7 — How a query actually works

**Content**

The tables are deliberately split apart. `JOIN` is how they are put back
together for reading — on demand, every time, without giving up the split.

Take the question *"which shops work in plumbing?"* The answer lives in three
tables and none of them holds it alone.

```sql
SELECT s.name_ar, t.name_ar
FROM shop s
JOIN shop_trade st ON st.shop_id = s.id
JOIN trade t ON t.id = st.trade_id
WHERE t.name_ar = 'السباكة';
```

**Read each line as a sentence:**

1. `FROM shop` — start with all 8 shops
2. `JOIN shop_trade ON ...` — pair each shop with its link rows. **8 rows become 10**, because الإتقان matches three links, one per trade
3. `JOIN trade ON ...` — attach the trade's name. Still 10 rows, now wider
4. `WHERE ...` — discard everything that isn't plumbing. **Down to 2 rows**
5. `SELECT` — choose which columns come back

**Two facts most people get wrong:**

- **SQL does not run in the order it is written.** `SELECT` is written first and
  executes *last* — the database must assemble and filter the rows before it can
  know which columns to return.
- **A `JOIN` creates nothing.** It writes no table and leaves nothing behind. The
  result is assembled in memory, sent to the browser, and discarded. Run it a
  hundred times and the database is byte-for-byte identical.

**Visual / animation**

Use the **join simulator** — it was built for exactly this:
https://claude.ai/code/artifact/a4e30527-0b59-4fcb-94f2-008ae6300590

Press *Play* and it steps through all 80 row comparisons: the outer pointer
walks down `shop`, the inner pointer scans `shop_trade`, each comparison shows
the two numbers and lands on **keep** or **discard**, and the result set fills
up from 0 to 10 rows. Watch shop 8 — it is the only one that hits three times.

Fallback if the room has no internet: screen-record it beforehand, or use the
static walkthrough at
https://claude.ai/code/artifact/a8c67faa-9ee0-4c4b-9aef-3c24e2acf786
which has the same content as fixed diagrams, including the written-order
vs execution-order crossing.

---

# Slide 8 — From query to screen: how a page is built

**Content**

`queries.sql` holds every query the app runs, written and tested before any
Python existed. **Its output is not stored anywhere** — that is the point of
slide 7. Each query is text that Python hands to Postgres; Postgres returns rows;
Python turns them into a page and forgets them.

**The path a click takes — four steps:**

```
1. Browser asks for  /trades/1
2. FastAPI matches the route  @app.get("/trades/{trade_id}")
3. That function runs the SQL from queries.sql, with 1 passed as a parameter
4. The rows go into trade.html, which renders to HTML and is sent back
```

**The app has 9 route handlers** covering: the home page and search, one trade,
one shop, add a shop, edit a shop, and add a branch.

**Where the data actually lands on screen:** the route passes a Python list to
the template, and Jinja loops over it:

```html
{% for t in trades %}
  <div class="card"><h3>{{ t.name_ar }}</h3></div>
{% endfor %}
```

One block written; seven cards rendered, because the database returned seven
rows. Add an eighth category to the database and the page grows by itself — no
HTML is edited.

**One safety rule that runs through all of it:** every value passed to SQL goes
as a parameter (`%s`), never glued into the string. That is what makes SQL
injection impossible — a search for `'; DROP TABLE shop;--` returns zero results
and leaves the database untouched.

**Visual / animation**

A four-stage pipeline animating left to right: a browser URL bar → a Python
function lighting up → a SQL statement flying into a database cylinder → rows
flying back → an HTML page assembling card by card → the finished
`03-trade.png` screenshot. Loop it once slowly, then once fast.

Then a short second beat: the same pipeline with `'; DROP TABLE shop;--` typed
in the search box — it travels as an inert grey blob labelled "parameter", the
database shrugs, and zero results come back.

---

# Slide 9 — Search

**Content**

Search runs on the home page as `GET /?q=...` and matches Arabic *or* English
names across both categories and shops:

```sql
SELECT * FROM shop
WHERE name_ar ILIKE %s OR name_en ILIKE %s
ORDER BY name_ar;
```

- `ILIKE` is case-insensitive matching
- `%` wraps the search term to mean "anything before or after"
- The `%` lives in the **value**, never in the SQL string — same parameter rule

Searching «سباك» finds مؤسسة النور للسباكة even though the word is only part of
the name.

**Visual / animation**

A cursor types «سباك» into the search box letter by letter, presses Enter, and
the results grid re-flows into place — go from `01-home.png` to `02-search.png`
with the cards animating between the two states.

---

# Slide 10 — Writing data back

**Content**

Reading is half a database. The app also creates shops, edits them, and adds
branches — and each write is where the constraints prove themselves.

**Adding a shop is two inserts that must both succeed:** the shop itself, and
its link row in `shop_trade`. If the second failed on its own, the shop would
belong to no category and appear on no page — invisible the moment it was
created. So both run inside **one transaction**:

```python
with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        cur.execute("INSERT INTO shop ... RETURNING id;", ...)
        shop_id = cur.fetchone()[0]
        cur.execute("INSERT INTO shop_trade (shop_id, trade_id) VALUES (%s, %s);", ...)
```

Either both are written or neither is. A half-created shop cannot exist.

**Validation happens twice, deliberately.** The form checks the phone number
before inserting so the user gets a readable Arabic message; the database checks
it again with the `CHECK` constraint so no other code path can slip a bad value
past. The friendly message is a convenience; the constraint is the guarantee.

**Visual / animation**

The add-shop form (`05-add-shop.png`) with a cursor filling fields and picking a
category from the dropdown. On submit, two rows fly into two different tables
simultaneously, joined by a bracket labelled «معاملة واحدة» (one transaction).
Then replay it with the second insert failing — a red X — and **both** rows
rewind and vanish. Then the error case: a bad phone number, and a red Arabic
message appearing under the field.

---

# Slide 11 — The seed file, and why it is not part of the database

**Content**

`seed.sql` is 60 lines of `INSERT` statements — 55 rows of realistic sample data:
shops with and without commercial registers, branches across Cairo, Giza and
Alexandria, employees with and without national IDs.

**It is not part of the database.** Delete it and the database is unchanged. The
distinction matters:

- **`schema.sql` is the structure.** Without it there is no database.
- **`seed.sql` is example content.** It exists so that anyone can rebuild a
  working copy in seconds, and so we could test with data that has the awkward
  cases in it deliberately.

**Two files, four commands, a full rebuild from nothing:**

```bash
dropdb trades_db && createdb trades_db
psql trades_db -f schema.sql
psql trades_db -f seed.sql
```

That reproducibility is why the seed exists. Anyone on the team — or the
examiner — gets a byte-identical database on their own machine.

**The awkward cases were planted on purpose.** عم سيد للأعمال المنزلية has no
commercial register, no bank account and no English name; two branches share one
central phone number. Testing against tidy data proves nothing.

**How you would load real data instead — from Excel:** the same tables, a
different door in. Export the sheet to CSV and let Postgres read it directly:

```sql
\copy shop(name_ar, name_en, commercial_register, bank_account, technical_capacity)
  FROM 'shops.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
```

`COPY` is built for bulk and is far faster than one `INSERT` per row. For a
messier sheet — where one column holds several trades per shop, or the phone
numbers need cleaning — the usual approach is a short Python script with
`openpyxl` or `pandas` to read the file, tidy each row, and insert it. **The
constraints then act as the import's quality gate:** any row with a malformed
phone or a duplicate register is rejected at the door rather than quietly
polluting the data.

**Visual / animation**

An Excel sheet on the left, rows highlighting one by one and flying rightward
into the five table boxes, each snapping into its correct table. Then a
deliberate failure: one row with a red phone number bounces off the `branch`
table and lands in a "rejected" tray, while the rest flow through. Underneath,
a counter: «55 صف — 0 خطأ».

---

# Slide 12 — How we divided the work

**Content**

Three people, three layers, one contract agreed before any code was written.

| Member | Owns | Delivered |
|---|---|---|
| **Mohamed** | Database | `schema.sql` (5 tables), `seed.sql` (55 rows), the ERD, `queries.sql` |
| **Wageh** | Backend | The routes, the shop+trade transaction, the branch flow, validation |
| **Bola** | Frontend | `base.html` and the page templates, Bootstrap RTL layout, search UI |

**The thing that made parallel work possible: `ENDPOINTS.md`.** It fixed the URL
of every page, what each one shows, and the exact SQL behind it — *before*
anyone opened an editor. That meant the backend could be written against a
database that wasn't finished, and the pages against endpoints that didn't
answer yet. When we connected them, they fit.

**What we would do differently:** two problems both traced to the same cause —
someone editing a file they didn't own without running the app. A page was once
replaced with hardcoded content that looked right but no longer read from the
database, and a local database password was committed to the repository. Both
were caught in review before submission. The fix is a habit, not a tool: **run
the app before you push.**

**Visual / animation**

Three lanes running left to right in parallel, each with its owner's name and a
progress bar filling. `ENDPOINTS.md` sits as a vertical dashed line at the very
start that all three lanes touch before diverging. At the right the three lanes
converge into one working screenshot. Then a brief "review" stamp catching two
red items and pulling them out of the merge.

---

# Slide 13 — Why GitHub

**Content**

**The version history is the safety net.** Every change is a commit with an
author and a reason. When a page was replaced with something that broke the
database link, reverting it was one command and nothing else was lost. Without
that, the only recovery is remembering what the file used to say.

**Branches keep unfinished work out of everyone's way.** Each person worked on
their own branch and merged when it was ready, so nobody's half-finished code
blocked anyone else.

**Issues turned "the site is broken" into assigned, specific work.** Seven
issues, each with the exact code to write and how to verify it, each assigned to
one person. All seven are closed.

**The review step caught what testing didn't.** Every merge was read before it
landed — that is how the committed password and the 500-error form were found.

**Visual / animation**

The GitHub repository page scrolling, then the commit graph drawing itself
branch by branch — three coloured lines diverging and merging back into `main`.
Then the issues list, with each of the seven issues stamping **closed** in
sequence, ending on «7 مغلقة».

Live if there's internet: https://github.com/Mo7ammedMajdy/trades-directory

---

# Slide 14 — Close / demo

**Content**

What exists, in numbers: **5 tables, 55 rows, 9 routes, 4 pages, 7 issues
closed, 3 contributors.**

What the database guarantees that an ordinary app cannot: no orphan branches, no
duplicate commercial registers, no malformed phone numbers, no half-created
shops — enforced on every write, from every direction, by the database itself.

**Then demo it live:** home page → search «سباك» → open الإتقان → show its three
branches and three trades → add a shop and watch it appear under its category.

**Land on `/shops/8`.** That one page displays all five tables simultaneously:
the shop's own record, the trades it is linked to through `shop_trade`, each of
its branches, and the employees inside each branch with a staff count on every
one. If the examiner asks "show me your database working", this is the page.

**Visual / animation**

The five numbers counting up from zero. Then hand over to the live app.

---

## Notes for whoever builds the deck

- **Arabic is the primary language and the layout is RTL.** Set slide direction
  accordingly; keep code blocks and SQL LTR inside RTL slides or they will
  scramble.
- **Every screenshot is real** — no mockups needed, and it is worth saying so.
- **Slide 5 (three rejected inserts) and slide 7 (the join simulator) are the two
  strongest moments.** Give them time; cut elsewhere if you must.
- **Have offline fallbacks.** The artifact links and the GitHub page need
  internet. Screen-record both beforehand — the app itself runs fully offline,
  Bootstrap included.
- If the deck must be shorter, merge slides 2 and 3 (why a database, why
  Postgres) and drop slide 9 (search folds into the demo).
