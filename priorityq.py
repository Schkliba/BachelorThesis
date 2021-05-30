import heapq
class MinPriorityQueue(object):
    def __init__(self):
        self.queue = []

    def __str__(self):
        return ' '.join([str(i) for i in self.queue])

        # for checking if the queue is empty

    def isEmpty(self):
        return len(self.queue) == 0

    # for inserting an element in the queue
    def insert(self, data:tuple):
        self.queue.append(data)

        # for popping an element based on Priority

    def pop(self):
        try:
            min_i=0
            min,obj = self.queue[0]
            for i in range(len(self.queue)):
                n,obj = self.queue[i]
                if n < min:
                    min = n
                    min_i = i
            item = self.queue[min_i]
            del self.queue[min_i]
            return item
        except IndexError:
            print("InderError")
            exit()