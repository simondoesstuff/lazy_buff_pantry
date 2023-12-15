import config from './config.json'
// the config contains the credentials and additional fields:
//  day, t1, t2 (day of week, start time, end time)


describe('Registration', () => {
    it('primary', () => {
        cy.visit('https://colorado.givepulse.com/group/624636-Buff-Pantry')

        // go to colorado edu login
        cy.log(`Logging in as ${config.identiKey}`)
        cy.get('button[aria-label="Navbar Profile Menu "]').first().click()
        cy.get('a').contains('Log In').first().click()
        cy.get('.btn-sso').click()

        // login to colorado edu
        cy.origin('https://fedauth.colorado.edu', {
            args: {
                'user': config.identiKey,
                'pass': config.password
            }
        }, ({user, pass}) => {
            cy.get('input#username').type(user)
            cy.get('input#password').type(pass)
            cy.get('button[type="submit"]').first().click()
        });
        cy.log("Logged in to colorado.edu")

        // returned to givepulse
        cy.wait(2000)
        cy.visit('https://colorado.givepulse.com/group/events/624636')

        // apparently once you enter classic mode, it permanently remembers
        // const profileButton = cy.get('header > div > div > div > div')
        // profileButton.eq(1).find('button').eq(1)
        // profileButton.click();
        // profileButton.parent().find('ul > a').eq(6).click();

        // select "appointment" button
        cy.get('div#eventDiv').find('a').first()
            .invoke('attr', 'href')
            .then(href => {
                const url = 'https://colorado.givepulse.com' + href;
                cy.visit(url);
            });

        // select "register" button
        cy.get('div.sidebar-buttons').find('a.btn').first().click();

        // sift through available appointments
        cy.log("Looking for appointment");
        cy.get('div.shift-item-container').each(($el) => {
            const check = $el.find('input[type="checkbox"]');
            if (check.is(':checked')
                || check.is(':disabled'))
                return;

            const label = $el.find('label.shift-item-label')
            const title = label.text();
            const spans = label.find('span');
            const dayStr = spans.eq(0).text();
            const timeStr = spans.eq(1).text();
            const day = /\s*(\w{3}),/.exec(dayStr)[1];
            if (day !== config.day) return;

            const [_, t1, t2] = /\s*(\d):.+(\d):/.exec(timeStr);
            if (t1 !== config.t1 || t2 !== config.t2) return;

            // register for all matching appointments
            cy.log('Found one!', title);
            cy.wrap(check).click();
        });

        cy.get('button').contains('Continue').click();

        // accept TOS if necessary
        cy.get('body')
            .then($body => {
                if ($body.find('div#termsOfServiceModal').length === 0) return;

                cy.get('div#event_tos')
                    .find('input[type="checkbox"]')
                    .then($el => {
                        if ($el.is(':checked')) return;
                        cy.wrap($el).first().click();
                    });
            });


        // register ✅
        cy.get('button').contains(/Continue|Update/).click();
        cy.log("Registered! 🎉");
    })
})