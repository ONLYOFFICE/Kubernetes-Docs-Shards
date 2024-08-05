#!/bin/bash
for i in `kubectl get pod | grep -i documentserver | awk '{print $1}'`; do
  kubectl logs $i > $i.txt
done
