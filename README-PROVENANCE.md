# What does "provenance" mean here?

Background:
- [Characterizing Provenance in Visualization and Data Analysis: An
Organizational Framework of Provenance Types and Purposes](http://people.cs.vt.edu/~eragan12/papers/Ragan_VAST2015.pdf)
- [From Visual Exploration to Storytelling and Back Again](http://caleydo.org/publications/2016_eurovis_clue/)

"Provenance" is important in understanding complex data sets, but the term has multiple, distinct senses.
*Refinery* has a sophisticated UI for understanding data provenance:
What was the origin of the data?
How have automated workflows generated derivative data? 
As we begin to support pluggable visualizations in *Refinery*, we are still interested in provenance,
and in the most abstract sense we are still dealing with the same underlying DAG data structures,
but the meaning and use of provence here is sufficiently distinct that we should not conflate the two:
We should not overload the existing provenance UI, and for the public documentation, **we might
ask whether distict terms would be more clear**. ("Workflows"; "Histories"; "Paths"; ...?)
(Besides the cognitive load to the user, in this case there is cognitive load on the software developer
to be considered: The *Refinery* codebase is already complex,
and I want to isolate new visualization work from that complexity.)

- Visualizations, like workflows, have source data, but it might not make sense to root the provenance
on that data:
    - If input data is taken as a root node, the root is a different type than all the other nodes in the interior of the graph.
    - Work in a visualization tool might be connected less to any particular data set, but instead be concerned with creation of a state in the tool which enables comparison of multiple data sets.
- Visualizations, like workflows, have discrete states, but:
    - It may be much less clear what states really matter.
    - And, there may be many more states, making the visual presentation of past states, and the inference of their rationale, more difficult.
- Visualization provenance, like a workflow, can be structured as a DAG, but:
    - It actually may just be a tree.
    - The history of exploration might not be closely connected to the story a researcher actually comes to understand.

## User stories

We can only address a small fraction of these: The point is to make our priorities explicit,
and potentially to identify overlaps between stories that could multiply the usefulness
of particular features.

- Researcher has data, explores it in a visualization, and finds particular settings which highlight an interesting pattern.
    - Researcher would like to know if the pattern is an artifact of the workflow, and so runs a different workflow on the same source data.
    - Or errors are identified in the processing of the first set, and new, better data is available.
    - Or new unrelated data comes in from an entirely new source: 
        - Researcher would like to view the new data with the same settings.
        - Researcher would like to compare the old and the new data with the same settings.
    - Or the researcher suspects that the pattern is an artifact of the visualization tool.
        - Researcher would like to view the same data, with the same settings, but with a different tool.
- Researcher has multiple data sets. After visualizing them, notices that there are distinct partitions.
    - Researcher would like to see if the data provenance or other data set metadata helps to explain the partition.
    - Researcher would like to identify and add new data sets with characteristics similar to one of the partitions.
- Researcher uses visualization tool to integrate diverse data sets.
    - And researcher would like to export in a reproducible way (back to Refinery) the combined data so that further analysis can be done.
    - At a latter point researcher realizes that a tweak to the parameters would be useful.
        - Researcher would like to re-export with just one settings change.
- Researchers A and B begin with the same data set:
    - They would like to work in parallel on the same visualization: Imagine a google hangout where they take turns exploring a visualization.
    - They will be working at the same time, but do not want to interfere with each other.
        - And, perhaps, at the end, each of them has some settings which are particularly useful, and they would like to combine components of their visualizations.
- Researcher A explores range of possibilities and forms a hypothesis.
    - At a latter date, Researcher B would like to know whether A considered a particular possibility.
- Researcher has explored a visualization and has formed a hypothesis.
    - The next day a new version of the tool becomes available,
    - Or, new reference data becomes available:
        - Researcher would like to replay the same steps, but with the latest software and data.
        
## Affordances and implementation possibilities

