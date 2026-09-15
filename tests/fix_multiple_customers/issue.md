Incorrect name resolution

Reported:
Message -> @sale jorge arias clavijo 9788414417805 9788414434208
Answer <- 🤖 Multiple customers match jorge arias clavijo

Same:
@buy dismalibro 9788414417805
🤖 Multiple suppliers match dismalibro

After check in odoo server confirmed than only one user can match the name
https://guadalstore.com/web#id=55887&cids=1-2&menu_id=229&action=343&model=res.partner&view_type=form

Probably related: https://github.com/Guadalsistema/guadalbot/issues/44

Requirements:
- using TDD modify e2e test test-buy.yml and test-sale.yml to reproduce the issue and fix it
- Improve the logging to debug the multiple suppliers / customers find

Save the analisys and implementation steps into the file .scratch/fix-multiple-customers.md
