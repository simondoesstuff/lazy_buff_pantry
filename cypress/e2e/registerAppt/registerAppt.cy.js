import config from './config.json'


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

        let results = [];
        { // appointment selection
            let appointmentIndex = new Map();

            const regexDay = /(\w{3}),\s*(\w{3}) (\d{1,2})/;
            const regexTime = /(\d{1,2}:\d{2}[ap]m).*-.*(\d{1,2}:\d{2}[ap]m)/;

            // 1. index all available appointments
            cy.get('div.shift-item-container').each(($el) => {
                const checkElement = $el.find('input[type="checkbox"]');
                if (checkElement.is(':disabled')) return;

                const label = $el.find('label.shift-item-label')
                const spans = label.find('span');
                const dayStr = spans.eq(0).text();
                const timeStr = spans.eq(1).text();

                const [_1, dayOfWeek, month, dayOfMonth] = regexDay.exec(dayStr);
                const [_2, t1, t2] = regexTime.exec(timeStr);
                const title = `${month} ${dayOfMonth}, ${dayOfWeek} ${t1} - ${t2}`
                const checkedAlready = checkElement.is(':checked');
                cy.log(`Candidate appointment indexed: ${title}`);

                const key = `${month} ${dayOfMonth}`;
                const cache = appointmentIndex.get(key) ?? [];
                const entry = {
                    title,
                    dayOfWeek,
                    dayOfMonth,
                    t1,
                    t2,
                    checkedAlready,
                    checkElement
                }

                cache.push(entry);
                appointmentIndex.set(key, cache);
            }).then(() => {

                // 2. find appointments that match the specified criteria

                cy.log(`Found ${appointmentIndex.size} days with appointments`);

                let lastApptDay = -90; // effectively infinity (days)

                // find the last appointment day
                for (const appts of appointmentIndex.values()) {
                    for (const appt of appts) {
                        if (appt.checkedAlready) {
                            // skip days that already have an appointment
                            if (appt.dayOfMonth > lastApptDay) lastApptDay = appt.dayOfMonth;
                        }
                    }
                }

                for (const target of config.times) {
                    dayLoop: for (const appts of appointmentIndex.values()) {
                        /*  Rules:
                                One appointment per day.
                                Only book appointments that match the specified criteria.
                                Multiple candidates? Pick the highest priority given by the config.
                         */

                        // (appts is at least length 1)
                        const dayOfMonth = appts[0].dayOfMonth;
                        const dayOfWeek = appts[0].dayOfWeek;

                        if (dayOfWeek !== target.day) continue;
                        if (dayOfMonth - lastApptDay < config.minDayGap) continue;

                        for (const appt of appts) {
                            if (appt.checkedAlready) continue dayLoop;
                        }

                        for (const appt of appts) {
                            if (appt.t1 !== target.t1) continue;
                            if (appt.t2 !== target.t2) continue;

                            // found a match!
                            cy.log(`Registering for ${appt.title}`);

                            if (appt.dayOfMonth > lastApptDay) {
                                lastApptDay = appt.dayOfMonth;
                            }

                            results.push(appt);
                            cy.wrap(appt.checkElement).click();
                            continue dayLoop;
                        }
                    }
                }
            });
        }

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

        cy.get('button')
            .contains(/Continue|Update/)
            .click()
            .then(() => {
                cy.log(`Made ${results.length} appointments.`);
                cy.log("Registered! 🎉");
            });

        // log the results

        if (!config.logFile) return;

        // todo the user will need to create the log
        cy.readFile(config.logFile, 'ascii').then(log => {
            const now = new Date();
            const dateStr = now.toLocaleDateString();
            const timeStr = now.toLocaleTimeString();
            let entry = `\n${dateStr} ${timeStr}`;

            if (results.length === 0) {
                entry += '\n  - no appointments found.';
            } else {
                for (const result of results) {
                    entry += `\n  + new appointment: ${result.title}.`;
                }
            }

            cy.writeFile(config.logFile, log + entry, 'ascii');
        });
    })
})