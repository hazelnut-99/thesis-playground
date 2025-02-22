# Slab Rebalance in CacheLib
[Doc1](https://cachelib.org/docs/Cache_Library_User_Guides/pool_rebalance_strategy/) </br>
[Doc2](https://cachelib.org/docs/Cache_Library_Architecture_Guide/slab_rebalancing) </br>
**Terminology**:
AC: Allocation Class

## High-level overview
There is a background daemon thread `PoolRebalancer` that gets invoked periodically. Upon invocation, it picks a *victim AC* and a *receiver AC*, moves a slab from the *victim AC* to the *receiver AC*. Note that *receiver AC* isn't necessary, and when the *receiver AC* isn't specified, 
the slab from the *victim AC* will be returned to the pool.

CacheLib provides several slab rebalancing strategies, they differ in how they choose the *victim AC* and *receiver AC*. Here we have a taste of the main idea behind each strategy-we'll dive into details later.

 - **Default strategy**: only interested in allocation failures 
	 - Pick receiver based on *most allocation failures*.
	 - Pick victim by *max number of slabs (free  +  used).*
 - **LRU Tail Age strategy**: based on tail age
	 - Pick receiver based on *min tail age*.
	 - Pick victim based on *max tail age*.
 - **Hits Per Slab strategy**: based on total hit count of ACs and uses a *`delta_hit`* metric. `delta_hit = hit_count(current) - hit_count(at_last_rebalance) / hit_count(current)`, a high `delta_hit` value indicates increasing popularity. 
	 - Pick receiver based on *max delta_hit* (increasing popularity).
	 - Pick victim based on *min delta_hit* (decreasing popularity). 
 - **Marginal Hits Per Slab strategy**: similar to HitsPerSlab, but instead of considering the toal hit count of ACs, it considers the hit count of the *tail* of each AC. (only works in combination with LRU2Q)
	 - Pick receiver based on *max tail delta_hit* (increasing popularity).
	 - Pick victim based on *min tail delta_hit* (decreasing popularity).
 - **Free Mem strategy**: it doesn't specify receiver, will return the slab from the victim AC to the pool
	 - Pick victim based on the *max free memory*
 - **Random strategy**: both victim and receiver are chosen randomly.

## Overall Workflow

    1. If poolRebalancerFreeAllocThreshold > 0:
        a. Pick an AC with most free memory (needs to be above the threshold) as the victim.
        b. Release a slab from the victim AC.
        c. If not all slabs are allocated in the pool, return (rebalance complete).
    
    2. If there exists an allocation class (AC) with allocation failures:
        a. Select the AC with the most allocation failures as the receiver.
        
        b. If no rebalance strategy is configured:
            i. Pick the AC with the most slabs as the victim (default).
        c. Else:
            i. Use the strategy-specific implementation to pick the victim.
    
        d. If both a victim and a receiver are found, return (rebalance complete).
    
    3. Otherwise:
        a. Use the strategy-specific implementation to pick both a victim and a receiver.





## Parameters
### Top-level 
- **poolRebalanceInterval**
	- default value: 1 sec
	- semantics: sleep interval for the `PoolRebalancer`
- **poolRebalancerFreeAllocThreshold** 
	- default value: 0
	- semantics: Free slabs pro-actively if the ratio of number of freeallocs to the number of allocs per slab in a slab class is above this threshold. A value of 0 (which is by-default) means, this feature is disabled. If enabled, it will release a slab from the AC with highest free alloc ratio (needs to be above this threshold), and if successful, the rebalancer will return directly.  **This works before and independently** of other rebalance strategies.
- **poolRebalancerDisableForcedWakeUp**
	- default value: false
	- semantics: if false, upon detecting allocation failures, the `PoolRebalancer` will be waked up (event-driven wake-up in addition to periodic wake-ups)

### Strategy-specific
#### LRU Tail Age
- **minSlabs**
	- default value: 1
	- semantics: min number of slabs to retain in every AC. ACs with fewer than `minSlabs` slabs don't have victim candidacy.
- **numSlabsFreeMem**
	- default value: 3
	- semantics: if there are ACs with >= `numSlabsFreeMem` free slabs, we will pick the AC with the max free slab count as the victim. **If we can find a victim in this way, the pick-by-max-tail-age victim-choosing logic will be skipped.**
- **slabProjectionLength**
	- default value: 1
	- semantics: when looking at the tail age, if slabProjectionLength = 1, we move one step forward from the tail and get the second-to-last node's age, if slabProjectionLength = 2, we move two step forward from the tail and get the third-to-last node's age.
- **tailAgeDifferenceRatio**
	- default value: 0.25
	- semantics: the relative tail age difference (diff / victim tail age) between the chosen victim and receiver must be above this threshold 
- **minTailAgeDifference**
	- default value: 100 (todo check unit)
	- semantics: the absolute tail age difference between the chosen victim and receiver must be above this threshold

#### Hits Per Slab
In addition to hit count, it also uses tail age as filters (to ensure some level of fairness by guaranteeing some eviction age).
- **minSlabs** and **numSlabsFreeMem** works similarly as *LRU Tail Age*
- **minLruTailAge**
	- default value: 0
	- semantics: min tail age for an AC to be eligible to be a victim
- **maxLruTailAge**
	- default value: 0
	- semantics: max tail age for an allocation class to be excluded from being a receiver
- **diffRatio**(default: 0.1), **minDiff**(default: 100)
	- relative and absolute `delta_hit` diff threshold between the chosen victim and receiver.

#### Marginal Hits Per Slab 
This strategy ranks ACs using the `tail delta hit`, pick the higest and lowest rank as the victim and receiver. In addition to tail hit count, it also used total slabs free slabs as filters.
- **minSlabs**: default value: 1, same as above. ACs with fewer than `minSlabs` slabs don't have victim candidacy.
- **movingAverageParam**
	- default value: 1
	- semantics: claimed to be the parameter for moving average, to smooth the ranking. (I didn't understand the point of this parameter, opened a [GitHub discussion](https://github.com/facebook/CacheLib/discussions/376))
- **maxFreeMemSlabs**
	- default value: 1
	- semantics: an AC can be a receiver only if its free slabs is below this threshold.

#### Free Mem
 - **minSlabs**: default value: 1, same as above. 
 - **maxUnAllocatedSlabs**
	 - default value: 1000
	 - semantics: if the pool’s unallocated slabs > maxUnAllocatedSlabs, won't rebalance anything and return directly.
 - **numFreeSlabs**
	 - default value: 3
	 - semantics: min free slabs for an AC to be victim.


### Additionals
- ACs with free slabs won't be chosen as receivers
- ACs that recently received slabs won't be chosen as victims (holdOff)


