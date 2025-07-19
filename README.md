sub directory problems??

keep it simple - testing is probably a bit much

delivery - probably not docker - would need to observe a directory outside of the container - a bit of a pain to do

fastAPI with uvicorn should provide a nice ASGI web server to handle async + multiple clients - make deployment easier as well.

## Assumptions and Limitations

- Following the description directly this is a one way sync - we're not concerned about there being "extra" files in the destination directory - if there are we leave them alone or overwrite them in the state of a conflict.
- Keep it lean - suggested time was 3-4 hours - no bells and whistles - no formal testing suit - testing performed as you would test something you would be building
- Evidence of different things tested to find limits - file sizes - path lengths (Windows :( ) - non ascii text - weird file types
- 

## Thought Process

As the intent of this is to observe how I work I believe leaving a section for notes / general thoughts may be useful.

- Little and often approach
- Keep it lean - stick to the brief - stick to the suggested time
- Don't re-invent the wheel