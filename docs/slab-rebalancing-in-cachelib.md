# Slab rebalance in CacheLib

  

[Doc1](https://cachelib.org/docs/Cache_Library_User_Guides/pool_rebalance_strategy/) </br>

  

[Doc2](https://cachelib.org/docs/Cache_Library_Architecture_Guide/slab_rebalancing) </br>

  

**Terminology**:

  

AC: Allocation Class

  

  

## High-level overview

CacheLib implements slab rebalancing through a background daemon thread called `PoolRebalancer` that periodically redistributes memory across Allocation Classes (ACs). The rebalancer's core operation involves looking at the internal statistics and selecting a "victim AC" to release memory and optionally a "receiver AC" to receive it.

| AC metric | Default | LRU tail age | Hits per slab | Marginal Hits | FreeMem |
|--|--|--|--|--|--|
| total slabs | Y |  |  |  |  |
| free memory |  | Y | Y |  | Y |
| tail age |  | Y | Y |  |  |  |
| hit count |  |  | Y |  |  |  |
| tail hit count |  |  |  | Y |  |  |


## Rebalancing Strategies

CacheLib provides several slab rebalancing strategies, they differ in how they choose the *victim AC* and *receiver AC*. Here's an overview-we'll dive into details later.

  

**Default strategy**: focuses on addressing allocation failures

- Receiver: AC with highest allocation failure count

- Victim: AC with maximum total slabs (free + used)

  

**LRU Tail Age strategy**: based on tail age (mimic a global LRU)

- Receiver: AC with minimum tail age

- Victim: AC with maximum tail age

  

**Hits Per Slab strategy**: to drive high objectwise-hitrate (can also ensure some fairness by setting eviction age threshold)

based on total hit count of ACs and uses a *`delta_hit`* metric.</br>

`delta_hit = hit_count(current) - hit_count(at_last_rebalance) / total_slab_count`, a high `delta_hit` value indicates increasing popularity. [\[source code\]](https://github.com/facebook/CacheLib/blob/fb79d6619cb4f0a5546b4cd6436a9ecdced0c32f/cachelib/allocator/RebalanceInfo.h#L133)

  

- Receiver: AC with highest delta_hit (indicating increasing popularity)

- Victim: AC with lowest delta_hit (indicating decreasing popularity)

  

**Marginal Hits strategy**: similar to HitsPerSlab, but instead of considering the toal hit count of ACs, it considers the hit count of the *tail* of each AC. (only works in combination with LRU2Q)

- Receiver: AC with highest tail delta_hit (indicating increasing popularity)

- Victim: AC with lowest tail delta_hit (indicating decreasing popularity)

  

**Free Mem strategy**: based on free memory

- Victim: AC with maximum free memory

- Doesn't specify receiver

  

**Random strategy**: both victim and receiver are chosen randomly.

  
### Counters different strategies rely on:



  

## Overall Workflow

  

[\[source code\]](https://github.com/facebook/CacheLib/blob/fb79d6619cb4f0a5546b4cd6436a9ecdced0c32f/cachelib/allocator/PoolRebalancer.cpp#L104)

  
  

1. (If poolRebalancerFreeAllocThreshold > 0), Free Memory Check

- identify ACs with free memory above threshold

- Release slab from AC with most free memory

- Exit if pool has unallocated slabs

  

2. Allocation Failure Resolution

- Select AC with most allocation failures as receiver

- For victim selection:

- Default: Choose AC with most slabs

- Otherwise: Use strategy-specific impl of victim selection

- Exit if both victim and receiver identified

  

3. Strategy-Specific Rebalancing

- Apply strategy-specific imp for selecting the victim and receiver AC.

  
  
  

## Parameters

### Top-level

-  **poolRebalanceInterval**

- default value: 1 sec

- semantics: sleep interval for the `PoolRebalancer`

-  **poolRebalancerFreeAllocThreshold**

- default value: 0

- semantics: Free slabs pro-actively if the ratio of number of freeallocs to the number of allocs per slab in a slab class is above this threshold. A value of 0 (which is by-default) means, this feature is disabled. If enabled, it will release a slab from the AC with highest free alloc ratio (needs to be above this threshold), and if successful, the rebalancer will return directly. **This works before and independently** of other rebalance strategies.

-  **poolRebalancerDisableForcedWakeUp**

- default value: false

- semantics: if false, upon detecting allocation failures, the `PoolRebalancer` will be waked up (event-driven wake-up in addition to periodic wake-ups)

  

### Strategy-specific

#### LRU Tail Age [\[source code\]](https://github.com/facebook/CacheLib/blob/fb79d6619cb4f0a5546b4cd6436a9ecdced0c32f/cachelib/allocator/LruTailAgeStrategy.cpp#L137)

-  **minSlabs**

- default value: 1

- semantics: min number of slabs to retain in every AC. ACs with fewer than `minSlabs` slabs don't have victim candidacy.

-  **numSlabsFreeMem**

- default value: 3

- semantics: if there are ACs with >= `numSlabsFreeMem` free slabs, we will pick the AC with the max free slab count as the victim. **If we can find a victim in this way, the pick-by-max-tail-age victim-choosing logic will be skipped.**

-  **slabProjectionLength**

- default value: 1

- semantics: when looking at the tail age, if slabProjectionLength = 1, we move one step forward from the tail and get the second-to-last node's age, if slabProjectionLength = 2, we move two step forward from the tail and get the third-to-last node's age.

-  **tailAgeDifferenceRatio**

- default value: 0.25

- semantics: the relative tail age difference (diff / victim tail age) between the chosen victim and receiver must be above this threshold

-  **minTailAgeDifference**

- default value: 100 (todo check unit)

- semantics: the absolute tail age difference between the chosen victim and receiver must be above this threshold

  

#### Hits Per Slab [\[source code\]](https://github.com/facebook/CacheLib/blob/fb79d6619cb4f0a5546b4cd6436a9ecdced0c32f/cachelib/allocator/HitsPerSlabStrategy.cpp#L26)

In addition to hit count, it also uses tail age as filters (to ensure some level of fairness by guaranteeing some eviction age).

-  **minSlabs** and **numSlabsFreeMem** works similarly as *LRU Tail Age*

-  **minLruTailAge**

- default value: 0

- semantics: min tail age for an AC to be eligible to be a victim

-  **maxLruTailAge**

- default value: 0

- semantics: max tail age for an allocation class to be excluded from being a receiver

-  **diffRatio**(default: 0.1), **minDiff**(default: 100)

- relative and absolute `delta_hit` diff threshold between the chosen victim and receiver.

  

#### Marginal Hits [\[source code\]](https://github.com/facebook/CacheLib/blob/fb79d6619cb4f0a5546b4cd6436a9ecdced0c32f/cachelib/allocator/RebalanceInfo.h#L133)

This strategy ranks ACs using the `tail delta hit`, pick the higest and lowest rank as the victim and receiver. In addition to tail hit count, it also used total slabs free slabs as filters.

-  **minSlabs**: default value: 1, same as above. ACs with fewer than `minSlabs` slabs don't have victim candidacy.

-  **movingAverageParam**

- default value: 0.3

- semantics: claimed to be the parameter for moving average, to smooth the ranking. (I didn't understand the point of this parameter, opened a [GitHub discussion](https://github.com/facebook/CacheLib/discussions/376))

-  **maxFreeMemSlabs**

- default value: 1

- semantics: an AC can be a receiver only if its free slabs is below this threshold.

  

#### Free Mem [\[source code\]](https://github.com/facebook/CacheLib/blob/fb79d6619cb4f0a5546b4cd6436a9ecdced0c32f/cachelib/allocator/FreeMemStrategy.cpp#L25)

-  **minSlabs**: default value: 1, same as above.

-  **maxUnAllocatedSlabs**

- default value: 1000

- semantics: if the pool’s unallocated slabs > maxUnAllocatedSlabs, won't rebalance anything and return directly.

-  **numFreeSlabs**

- default value: 3

- semantics: min free slabs for an AC to be victim.

  
  

### Additionals

- ACs with free slabs won't be chosen as receivers

- ACs that recently received slabs won't be chosen as victims (holdOff)