# Permissive-License WISP Implementations

Most WISP implementations are under AGPL, which is a great license for projects
like Puter or AnuraOS, but not ideal for service providers or SDK vendors which
may need to implement WISP in code bases with more permissive licenses.

This repository will be developed by me as I need to develop it, for example
if a service provider wants to integrate with Puter and it makes sense to use
the Wisp protocol in their integration.

I will also accept pull requests which provide any of the following:
- separating specific use-cases of WISP from WISP implementations
- adding WISP implementations for more languages

Eventually, however, I would like to do this:
- Model the WISP protocol in a software-readable format.
- Model how conversion between primatives and binary data
  is implemented in various programming languages
- Use the previous two items of work to implement a code
  generator that implements most of the required code
  (excluding boilerplate, package manifests, etc)
  for the actual WISP implementations.
