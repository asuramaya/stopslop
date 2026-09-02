Meridian Freight shipped software nine times a quarter. Each release cost the team a Saturday, and Priya Raghavan, who ran platform engineering, kept a paper checklist of forty-one steps taped inside a cabinet door in the ops room. Two people had to sign it before anyone touched production.

She bought Trellis in March 2024, a week after a release ran past midnight and the billing service came back pointed at the wrong database. Customers saw invoices belonging to other customers. Priya spent the next several days apologizing to accounts she had never spoken to, then went looking for a tool.

Her team moved the checklist into Trellis pipelines over six weeks. She cut the forty-one steps down to eleven automated stages plus one human approval on the production gate. Trellis runs the test suite and holds the built container until someone with the deploy role clicks through. Rollback takes ninety seconds, since Trellis keeps the previous three artifacts warm, and nobody has to reconstruct a release by hand at two in the morning anymore.

Meridian now deploys around fourteen times a week. Priya's on-call engineers stopped scheduling releases for weekends. Change failure rate dropped from 18 percent to 4 percent over the first two quarters, and when a deploy breaks, her team reverts before the support queue fills up. Marcus Bell joined as a backend engineer in August and shipped his first change on day three, where under the old process he would have waited five weeks for the next release window.

Priya kept the paper checklist in the cabinet. She points at it when new hires ask why the deploy button still needs a second person.
