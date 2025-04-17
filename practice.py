# Definition for singly-linked list.
from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
class Solution:
    def reverseKGroup(self, head: Optional[ListNode], k: int) -> Optional[ListNode]:
        def get_kth(curr, k):
            while curr and k > 0:
                curr = curr.next
                k -= 1
            return curr
        
        dummy = ListNode(0)
        dummy.next = head
        group_prev = dummy
        
        while True:
            kth = get_kth(group_prev, k)
            if not kth:
                break
            group_next = kth.next

            # Reverse the group
            prev = group_next
            curr = group_prev.next
            while curr != group_next:
                tmp = curr.next
                curr.next = prev
                prev = curr
                curr = tmp

            tmp = group_prev.next  # new end of the group
            group_prev.next = kth  # connect with reversed head
            group_prev = tmp       # move pointer for next group
        
        return dummy.next
        
        


omde = Solution().reverseKGroup(ListNode(1, ListNode(2, ListNode(3, ListNode(4, ListNode(5, None))))), 2)
while omde.next:
    print(omde.val)
    omde = omde.next