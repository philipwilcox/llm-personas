# Demo Planning


## TODOs


# TODO: NEXT STEPS
[ ] TODO: make a differently-nested dialogue persona: one sub-persona PER MOOD with different dialogue styles and a nested-"mood selection" subpersona that deals more explicitly with multiple-message-history-at-once (probably code driven)
[ ] TODO: unit testing/config - make things like Messenger optionally injectable for testing
[ ] # TODO: rewrite PersonaMessage to have "is_user" and "is_assistant" and "create_user" and "create_assistant" etc instead of doing type checks...
[ ] # TODO: do a console/interactive demo of dialogue generation
[ ] # TODO: nested nesting - add a concept of "originator" to ProposedPersonaResponse to allow proper passing up-the-chain in process_proposed_result
[ ] # TODO: be able to target methods INSIDE OF classes with Rewriter stuff
[ ] # TODO: also build out agent personas for things like "refactor method to be more testable (skill vs primitive as example)" and "write test case summaries" and "write test case from summary"
[ ] # TODO: can we do boardgame planning?
[ ] # TODO: test hydrating console from history; implement saving history after each step